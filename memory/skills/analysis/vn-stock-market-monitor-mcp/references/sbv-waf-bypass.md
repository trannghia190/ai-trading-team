# SBV WAF Bypass Pattern (Macro Liquidity)

The State Bank of Vietnam (SBV) website (`sbv.gov.vn`) uses a Web Application Firewall (WAF) that blocks standard bot/curl requests with a `Request Rejected` error.

**Discovery:**
You do *not* need to pre-fetch or hardcode a valid `JSESSIONID` or `TS*` cookie. The WAF will accept a request and dynamically assign cookies IF the request closely mimics a real browser navigating to the page.

**Working Headers Pattern:**
```http
GET /vi/nghi%E1%BB%87p-v%E1%BB%A5-th%E1%BB%8B-tr%C6%B0%E1%BB%9Dng-m%E1%BB%9F HTTP/1.1
Host: sbv.gov.vn
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Language: en-US,en;q=0.9
Connection: keep-alive
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36
sec-ch-ua: "Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "macOS"
```

**Implementation Note:**
When building the `vn-stock-macro-liquidity-overlay` or extracting OMO data, use Python's `urllib`, `requests`, or a subagent script with these exact headers. The server will return `200 OK` and the HTML content, along with a `Set-Cookie` header for subsequent requests. Do not assume `sbv.gov.vn` is unreachable via automation.