$tokenResponse = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/auth/token" -ContentType "application/json" -Body '{"username":"ops","password":"ops-demo-2026"}'
$headers = @{ "Authorization" = "Bearer $($tokenResponse.access_token)" }

Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/health" -Headers $headers
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/accounts?branch_code=MIL01" -Headers $headers
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/accounts/IT-1001" -Headers $headers
Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/accounts/IT-1001/transactions?limit=4" -Headers $headers
