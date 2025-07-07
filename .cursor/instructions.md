# Cosmos Gov‑Watcher SaaS – **Build Specs**

> **Goal** Ship a low‑touch SaaS that e‑mails paying users exactly **once per proposal** when the voting period opens on any Cosmos‑SDK chain they opted‑into, adding an LLM‑generated summary + voting recommendation driven by their own policy blurbs.
>
> • 12‑hour polling cadence • Annual (15 FET) subscription + 1 FET / extra‑chain • Runs on the AWS free/near‑free tier

---

## 0 – Quick architecture map

```mermaid
flowchart TD
    sub["SubscriptionAgent\n(Lambda)"]
    evt[Amazon EventBridge\nCron (12 h)]
    watch["WatcherAgent\n(Lambda, one per chain)"]
    analysis["AnalysisAgent\n(Lambda)"]
    mail["MailAgent\n(Lambda ⇒ SES)"]
    s3[(S3 Bucket logs)]
    db[(DynamoDB Subscriptions)]

    evt --> watch
    watch -->|NewProposal| analysis
    analysis -->|VoteAdvice| mail
    sub --> db
    watch --> s3
    analysis --> s3
    mail --> s3
```

*All four uAgents live in the same container image but are surfaced as **separate Lambda functions** (one handler each) ➜ you pay only for the **few seconds** they execute every 12 h.*

---

## 1 – AWS resource list (ultra‑cheap flavour)

| AWS resource             | Why                         | Cost notes                                                                                                                                                                                                  |
| ------------------------ | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Lambda (x4)**          | Run agents on‑demand        | Permanent free tier: 1 M invocations & 400 000 GB‑s / mo. Plenty at 2 invocations/day/chain                                                                                                                 |
| **EventBridge rule**     | Triggers Watcher every 12 h | 14 M scheduler invocations/mo free ([aws.amazon.com](https://aws.amazon.com/eventbridge/pricing/?utm_source=chatgpt.com))                                                                                   |
| **DynamoDB (on‑demand)** | Store subscriptions         | 25 GB & 25 RCU/WCU always‑free ([aws.amazon.com](https://aws.amazon.com/dynamodb/pricing/provisioned/?utm_source=chatgpt.com))                                                                              |
| **S3 Standard‑IA**       | Append‑only JSON logs       | First 5 GB/mo ≈ \$0.06; add 30‑day lifecycle to Glacier                                                                                                                                                     |
| **SES**                  | Transactional e‑mail        | 62 k msgs/mo free when invoked from Lambda ([stackoverflow.com](https://stackoverflow.com/questions/64648480/what-would-be-the-pricing-for-using-amazon-ses-from-a-lambda-function?utm_source=chatgpt.com)) |
| **Secrets Manager**      | Hold API keys               | \$0.40/secret/mo – keep only OPENAI & PRIVATE\_KEY                                                                                                                                                          |

Total =\~ **\$0–3 / month** for ≈ 500 paid users.

---

## 2 – Data model

### 2.1 DynamoDB table `GovSubscriptions`

| Field (PK = wallet) | Type        | Notes                                                     |
| ------------------- | ----------- | --------------------------------------------------------- |
| `wallet`            | `S`         | uAgents wallet address                                    |
| `email`             | `S`         | Verified SES destination                                  |
| `expires`           | `N` (epoch) | Annual subscription expiry                                |
| `chains`            | `SS`        | Set of cosmos chain IDs                                   |
| `policy`            | `S`         | JSON‑encoded list of policy blurbs                        |
| `last_notified`     | `M`         | map⟨chain→proposal\_id⟩ to ensure *one‑mail‑per‑proposal* |

### 2.2 S3 key scheme

```
logs/
  YYYY/MM/DD/
    <timestamp>_<lambda>_<request‑id>.json
```

Payload = raw Model.dict() + Lambda context.

---

## 3 – Lambda / uAgent handlers

> All code in `handler.py`; build once with **Docker multi‑stage** → single image ≈ 180 MB.

### 3.1 Common models  (`models.py`)

```python
class SubConfig(Model):
    email: str
    chains: list[str]
    policy_blurbs: list[str]

class NewProposal(Model):
    chain: str
    proposal_id: int
    title: str
    description: str

class VoteAdvice(Model):
    chain: str
    proposal_id: int
    decision: str  # YES / NO / ABSTAIN
    rationale: str
```

### 3.2 `SubscriptionAgent`

*Trigger:* API Gateway `POST /subscribe` → Lambda proxy → uAgent.

```python
@agent.on_message(model=SubConfig, replies=bool, payable=15)
async def register(ctx, sender, cfg: SubConfig):
    table.put_item(Item={
        'wallet': sender,
        'email': cfg.email,
        'chains': cfg.chains,
        'policy': json.dumps(cfg.policy_blurbs),
        'expires': int(time.time()) + 31536000,
        'last_notified': {}
    })
    await ctx.send(sender, True)
```

### 3.3 `WatcherAgent`

Lambda is scheduled **rate(12 hours)** via EventBridge; one environment var `CHAIN_ID` per deployment.

```python
@agent.on_interval(period=1)  # instant; Lambda itself is the scheduler
async def tick(ctx):
    last_id = int(os.getenv('LAST_ID', '0'))
    new = fetch_new_proposals(chain_id, last_id)
    for p in new:
        await ctx.send(analysis_addr, NewProposal(**p))
    if new:
        os.environ['LAST_ID'] = str(max(p['proposal_id'] for p in new))
```

### 3.4 `AnalysisAgent`

```python
@agent.on_message(model=NewProposal, replies=VoteAdvice)
async def analyse(ctx, sender, prop: NewProposal):
    for sub in paid_subs(prop.chain):
        prompt = build_prompt(prop, sub['policy'])
        gpt = openai.ChatCompletion.create(model=os.getenv('LLM','gpt-4o'), messages=[...])
        decision = parse_decision(gpt.choices[0].message.content)
        await ctx.send(mail_addr, VoteAdvice(...))
```

### 3.5 `MailAgent`

```python
@agent.on_message(model=VoteAdvice)
async def email(ctx, _, advice):
    if already_sent(advice.chain, advice.proposal_id, advice.target_wallet):
        return  # enforce one‑shot
    ses.send_email(...)
    put_log_to_s3()
    mark_sent()
```

---

## 4 – CloudFormation skeleton

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: Cosmos‑Gov‑Watcher
Parameters:
  DomainName: { Type: String }
  FromEmail:  { Type: String }
  OpenAIKey:  { Type: String, NoEcho: true }
  PrivateKey: { Type: String, NoEcho: true }
  AnnualFeeFET: { Type: Number, Default: 15 }
  ExtraChainFeeFET: { Type: Number, Default: 1 }

Resources:
  LogBucket:
    Type: AWS::S3::Bucket
    Properties:
      LifecycleConfiguration:
        Rules:
          - Id: Glacier
            Status: Enabled
            ExpirationInDays: 30

  SubTable:
    Type: AWS::DynamoDB::Table
    Properties:
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: wallet
          AttributeType: S
      KeySchema:
        - AttributeName: wallet
          KeyType: HASH

  GovWatcherImage:
    Type: AWS::ECR::Repository

  GovWatcherRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument: |
        { "Version":"2012-10-17", "Statement":[{"Effect":"Allow","Principal":{"Service":["lambda.amazonaws.com"]},"Action":"sts:AssumeRole"}] }
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: AccessAWS
          PolicyDocument: |
            {"Version":"2012-10-17","Statement":[
              {"Effect":"Allow","Action":["dynamodb:*"],"Resource":"*"},
              {"Effect":"Allow","Action":["s3:PutObject"],"Resource":"*"},
              {"Effect":"Allow","Action":["ses:SendEmail"],"Resource":"*"}
            ]}

  ## repeat: Four Lambda resources referencing same container & role
  ## … plus EventBridge rule with Target = Watcher Lambda and ScheduleExpression: rate(12 hours)

Outputs:
  ApiUrl: { Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/prod/" }
```

*Store the full YAML in `infra/stack.yml`; CI runs `aws cloudformation deploy --capabilities CAPABILITY_NAMED_IAM`.*

---

## 5 – Deployment pipeline (CLI‑only)

1. **Build & Push**   `docker build -t govwatcher . && aws ecr get-login-password|docker login … && docker push …`
2. **Deploy infra**   `aws cloudformation deploy --stack-name govwatcher --template-file infra/stack.yml --parameter-overrides DomainName=example.com FromEmail=no‑reply@example.com OpenAIKey=*** PrivateKey=***`
3. **Verify SES** domain & email.
4. **Test** with `uagents cli send --receiver <SubscriptionAgent> --model SubConfig '{…}'`.

---

## 6 – Pricing guideline for end‑users

* **Base plan:** 15 FET / year (≈ €6) gives 1 chain.
* **Add‑on:** +1 FET per extra chain (flat, no limit).
* **Fair‑use clause:** max 52 proposals/chain/year ➜ < 160 e‑mails even on heavy chains.

Break‑even vs. infra cost at \~5 users; margin >90 % afterwards.

---

## 7 – Admin run‑book

| Task              | Command                                                                                                   |
| ----------------- | --------------------------------------------------------------------------------------------------------- |
| Pause all e‑mails | `aws lambda update-function-configuration --function-name MailAgent --environment "Variables={PAUSED=1}"` |
| Add new chain     | Deploy additional Watcher Lambda with new `CHAIN_ID` env var; no infra change required.                   |
| Rotate OPENAI key | `aws secretsmanager put-secret-value --secret-id GovWatcher/OpenAI --secret-string …`                     |
| Restore logs      | `aws s3 cp s3://<bucket>/logs/… .`                                                                        |

---

## 8 – Optional UI

*Fastest*: rely on **Fetch DeltaV UI** – users can send `SubConfig` messages from the marketplace panel once your agents are listed.

*Alternative*: thin React SPA behind CloudFront + API Gateway calling `POST /subscribe`.

---

## 9 – Future ideas

* Switch Watcher polling to **WebSocket push** as more chains expose gRPC streams.
* Offer **Telegram/Discord DM** via an extra NotificationAgent.
* Bundle per‑chain vote forecasts into a paid dashboard (extra upsell).

---

### That’s it

Copy → adapt → deploy. You will be live in < 2 hrs (most of that is SES domain verification delay). Good luck and happy shipping! 🚀
