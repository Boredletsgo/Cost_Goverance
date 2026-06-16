# Connecting InfraMind to your own cloud

By default InfraMind runs in **mock mode** — every connector serves bundled sample
data, so you can explore the whole platform with zero cloud setup. When you're ready
to analyze a **real subscription**, switch a connector to **live mode**.

Live connectors are available today for **Azure** and **AWS**. Everything degrades
gracefully: if a live call fails (missing SDK, missing permission, transient error),
that data type silently falls back to mock data so the app keeps working.

> **Security:** Credentials are read from your environment only (`.env`, `az login`,
> AWS profile/role). InfraMind never writes secrets to disk. The runtime store only
> remembers the mock/live *toggle*, not credentials.

---

## 1. Install the cloud SDKs

```bash
cd backend
pip install -r requirements.txt -r requirements-cloud.txt
```

This adds `boto3` (AWS) and the `azure-identity` / `azure-mgmt-*` packages (Azure).

## 2. Authenticate

### Azure

Pick **one**:

- **Interactive (easiest):** `az login`
- **Service principal (CI / headless):** set in `.env`
  ```
  AZURE_TENANT_ID=...
  AZURE_CLIENT_ID=...
  AZURE_CLIENT_SECRET=...
  ```

Always set the target subscription:

```
AZURE_SUBSCRIPTION_ID=00000000-0000-0000-0000-000000000000
AZURE_MODE=live
```

**Required RBAC** on the subscription (read-only is enough):

| Data type | Role / permission |
|-----------|-------------------|
| Cost      | `Cost Management Reader` |
| Resources | `Reader` |
| Events    | `Reader` (Activity Log) |
| Security  | `Security Reader` (Microsoft Defender for Cloud) |

A subscription-level **Reader** + **Cost Management Reader** + **Security Reader**
covers all four.

### AWS

Pick **one**:

- **Shared profile (easiest):** `aws configure` (or `aws configure --profile myprofile`)
  ```
  AWS_PROFILE=myprofile
  ```
- **Explicit keys:** set in `.env`
  ```
  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
  AWS_SESSION_TOKEN=        # only for temporary creds
  ```
- **Instance role / env vars:** nothing to configure — boto3's default chain is used.

Set the region and enable live mode:

```
AWS_REGION=us-east-1
AWS_MODE=live
```

**Required IAM permissions** (read-only):

| Data type | Permissions |
|-----------|-------------|
| Cost      | `ce:GetCostAndUsage` |
| Resources | `tag:GetResources` |
| Events    | `cloudtrail:LookupEvents` |
| Security  | `securityhub:GetFindings` |

The AWS managed policies `ViewOnlyAccess` + `AWSSecurityHubReadOnlyAccess` are a
convenient superset. Cost Explorer must be enabled in the account.

## 3. Switch to live and ingest

You can do this from the UI or via `.env`:

- **UI:** open the **Setup** tab → flip the connector to **live** → **Test connection**
  → **Re-ingest data**.
- **`.env`:** set `AZURE_MODE=live` / `AWS_MODE=live`, restart, then call
  `POST /api/connectors/refresh` (or hit **Refresh** in the Connectors tab).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Setup shows *SDK missing* | `pip install -r requirements-cloud.txt` |
| Setup shows *credentials not set* | Run `az login` / `aws configure`, or set keys in `.env` |
| Test connection fails with auth error | Verify the subscription/region and that your identity has the roles above |
| Live mode but data looks like samples | A live call failed and fell back to mock — check backend logs for the warning |
| Azure cost returns nothing | Cost Management data can lag; ensure `Cost Management Reader` and a billing-enabled subscription |
| AWS cost returns nothing | Enable Cost Explorer in the AWS console (one-time, ~24h to populate) |

## How it works

Each cloud has a **mock** connector (`azure.py`, `aws.py`) and a **live** subclass
(`azure_live.py`, `aws_live.py`). The registry picks the live class only when the
connector's mode is `live` **and** the SDK is importable; otherwise it uses the mock
class. The live subclass overrides each data method, runs the synchronous vendor SDK
in a thread, and falls back to its mock parent on any exception. See
[docs/CONNECTORS.md](CONNECTORS.md) to add your own.
