const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 3000;
const API_URL = process.env.API_URL || "http://localhost:8000";

const server = http.createServer((req, res) => {

  if (req.url === "/healthz") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "healthy" }));
    return;
  }

  if (req.url === "/metrics") {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("# HELP web_up Web service availability\n# TYPE web_up gauge\nweb_up 1\n");
    return;
  }

  if (req.url.startsWith("/api/")) {
    const target = `${API_URL}${req.url.replace("/api", "")}`;
    const client = target.startsWith("https") ? https : http;

    client.get(target, (apiRes) => {
      res.writeHead(apiRes.statusCode, apiRes.headers);
      apiRes.pipe(res);
    }).on("error", () => {
      res.writeHead(502);
      res.end(JSON.stringify({ error: "API unavailable" }));
    });

    return;
  }

  const html = fs.readFileSync(
    path.join(__dirname, "index.html"),
    "utf8"
  );

  res.writeHead(200, { "Content-Type": "text/html" });
  res.end(html);
});

server.listen(PORT, () => {
  console.log(`Web server running on :${PORT}`);
});
