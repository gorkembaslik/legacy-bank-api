from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from .legacy_adapter import LegacyDataAdapter
from .models import Account, AccountStatusInfo, AccountSummary, AuthRequest, AuthToken, HealthResponse, Transaction
from .security import authenticate_user, issue_token, require_token, revoke_token

BASE_DIR = Path(__file__).resolve().parent.parent
adapter = LegacyDataAdapter(data_dir=BASE_DIR / "data")

app = FastAPI(
    title="Legacy Core Banking Adapter API",
    description=(
        "REST facade for exposing legacy core-banking exports to modern cloud-native services."
    ),
    version="1.0.0",
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def legacy_ui() -> str:
        return """
        <!doctype html>
        <html lang="it">
            <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <title>Banca Legacy - Console</title>
                <style>
                    body {
                        margin: 0;
                        font-family: "Courier New", monospace;
                        background: #f2f2e6;
                        color: #222;
                    }
                    .wrap {
                        max-width: 820px;
                        margin: 24px auto;
                        border: 2px solid #1f3a1f;
                        background: #fffff8;
                        padding: 16px;
                    }
                    h1 {
                        margin: 0 0 14px;
                        font-size: 20px;
                        background: #1f3a1f;
                        color: #fff;
                        padding: 8px;
                    }
                    .row {
                        display: flex;
                        gap: 8px;
                        margin-bottom: 8px;
                    }
                    input, button {
                        font-family: inherit;
                        font-size: 14px;
                        padding: 6px;
                        border: 1px solid #1f3a1f;
                    }
                    button {
                        background: #d8e8d8;
                        cursor: pointer;
                    }
                    pre {
                        background: #f7f7f0;
                        border: 1px solid #1f3a1f;
                        padding: 10px;
                        min-height: 220px;
                        overflow: auto;
                        white-space: pre-wrap;
                    }
                </style>
            </head>
            <body>
                <div class="wrap">
                    <h1>BANCA LEGACY - TERMINALE OPERATIVO</h1>
                    <div class="row">
                        <input id="username" value="ops" placeholder="username" />
                        <input id="password" type="password" value="ops-demo-2026" placeholder="password" />
                        <button onclick="login()">Login</button>
                        <button id="logoutBtn" onclick="logout()" disabled>Logout</button>
                    </div>
                    <div class="row">
                        <button id="accountsBtn" onclick="loadAccounts()" disabled>Conti</button>
                    </div>
                    <div class="row">
                        <input id="accountId" value="IT-1001" placeholder="account id" />
                        <button id="txBtn" onclick="loadTransactions()" disabled>Movimenti</button>
                        <button id="statusBtn" onclick="loadStatusInfo()" disabled>Info Stato</button>
                        <button id="healthBtn" onclick="loadHealth()" disabled>Stato Sistema</button>
                    </div>
                    <pre id="output">Pronto.</pre>
                </div>

                <script>
                    let token = "";
                    const output = document.getElementById("output");
                    const accountsBtn = document.getElementById("accountsBtn");
                    const txBtn = document.getElementById("txBtn");
                    const statusBtn = document.getElementById("statusBtn");
                    const healthBtn = document.getElementById("healthBtn");
                    const logoutBtn = document.getElementById("logoutBtn");

                    function setAuthenticatedState(isAuthenticated) {
                        accountsBtn.disabled = !isAuthenticated;
                        txBtn.disabled = !isAuthenticated;
                        statusBtn.disabled = !isAuthenticated;
                        healthBtn.disabled = !isAuthenticated;
                        logoutBtn.disabled = !isAuthenticated;
                    }

                    function show(data) {
                        output.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
                    }

                    async function login() {
                        const username = document.getElementById("username").value;
                        const password = document.getElementById("password").value;
                        const response = await fetch("/auth/token", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ username, password })
                        });
                        const data = await response.json();
                        if (!response.ok) {
                            token = "";
                            setAuthenticatedState(false);
                            show(data);
                            return;
                        }
                        token = data.access_token;
                        setAuthenticatedState(true);
                        show({ message: "Login riuscito", token_expires_in_seconds: data.expires_in_seconds });
                    }

                    async function logout() {
                        if (!token) {
                            show("Nessuna sessione attiva.");
                            return;
                        }
                        const response = await fetch("/auth/logout", {
                            method: "POST",
                            headers: { Authorization: `Bearer ${token}` }
                        });
                        token = "";
                        setAuthenticatedState(false);
                        if (!response.ok) {
                            show("Logout locale completato. Token già non valido lato server.");
                            return;
                        }
                        show("Logout completato.");
                    }

                    async function callApi(url) {
                        if (!token) {
                            show("Esegui login prima.");
                            return;
                        }
                        const response = await fetch(url, {
                            headers: { Authorization: `Bearer ${token}` }
                        });
                        const data = await response.json();
                        if (response.status === 401) {
                            token = "";
                            setAuthenticatedState(false);
                            show("Sessione non valida. Esegui nuovamente login.");
                            return;
                        }
                        show(data);
                    }

                    function loadAccounts() {
                        callApi("/accounts");
                    }

                    function loadTransactions() {
                        const accountId = document.getElementById("accountId").value;
                        callApi(`/accounts/${accountId}/transactions?limit=10`);
                    }

                    function loadStatusInfo() {
                        const accountId = document.getElementById("accountId").value;
                        callApi(`/accounts/${accountId}/status-info`);
                    }

                    function loadHealth() {
                        callApi("/health");
                    }
                </script>
            </body>
        </html>
        """


@app.post("/auth/token", response_model=AuthToken, tags=["auth"])
def login(payload: AuthRequest) -> AuthToken:
        if not authenticate_user(payload.username, payload.password):
                raise HTTPException(status_code=401, detail="Invalid credentials")

        token, expires_in = issue_token(payload.username)
        return AuthToken(access_token=token, expires_in_seconds=expires_in)


@app.post("/auth/logout", tags=["auth"])
def logout(token: str = Depends(require_token)) -> dict[str, str]:
    revoke_token(token)
    return {"status": "logged_out"}


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health_check(_: str = Depends(require_token)) -> HealthResponse:
    accounts = adapter.load_accounts()
    transactions = adapter.load_transactions()
    return HealthResponse(
        status="ok",
        legacy_source="nightly_csv_export",
        loaded_accounts=len(accounts),
        loaded_transactions=len(transactions),
    )


@app.get("/accounts", response_model=list[Account], tags=["accounts"])
def list_accounts(
    branch_code: str | None = Query(default=None),
    status: str | None = Query(default=None),
    _: str = Depends(require_token),
) -> list[Account]:
    accounts = adapter.load_accounts()

    if branch_code:
        accounts = [acc for acc in accounts if acc.branch_code == branch_code]

    if status:
        accounts = [acc for acc in accounts if acc.status.lower() == status.lower()]

    return accounts


@app.get("/accounts/{account_id}", response_model=AccountSummary, tags=["accounts"])
def get_account_summary(account_id: str, _: str = Depends(require_token)) -> AccountSummary:
    accounts = adapter.load_accounts()
    account = next((acc for acc in accounts if acc.account_id == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return AccountSummary(
        account_id=account.account_id,
        customer_name=account.customer_name,
        balance=account.balance,
        currency=account.currency,
        last_updated=adapter.latest_refresh_timestamp(),
    )


@app.get("/accounts/{account_id}/transactions", response_model=list[Transaction], tags=["transactions"])
def get_account_transactions(
    account_id: str,
    limit: int = Query(default=5, ge=1, le=100),
    _: str = Depends(require_token),
) -> list[Transaction]:
    transactions = adapter.load_transactions()
    filtered = [tx for tx in transactions if tx.account_id == account_id]
    sorted_transactions = sorted(filtered, key=lambda tx: tx.posted_at, reverse=True)
    return sorted_transactions[:limit]


@app.get("/accounts/{account_id}/status-info", response_model=AccountStatusInfo, tags=["accounts"])
def get_account_status_info(account_id: str, _: str = Depends(require_token)) -> AccountStatusInfo:
    status_items = adapter.load_account_status_info()
    status_item = next((item for item in status_items if item.account_id == account_id), None)
    if not status_item:
        raise HTTPException(status_code=404, detail="Status information not found")

    latest_activity = adapter.latest_transaction_activity(account_id)
    return status_item.model_copy(update={"last_customer_activity_at": latest_activity})
