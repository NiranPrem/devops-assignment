const http = require("http");
const https = require("https");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 3000;
const API_URL = process.env.API_URL || "http://api";

const server = http.createServer((req, res) => {

  if (req.url === "/healthz") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "healthy" }));
    return;
  }

  if (req.url === "/metrics") {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end(
      "# HELP web_up Web service availability\n" +
      "# TYPE web_up gauge\n" +
      "web_up 1\n"
    );
    return;
  }

  if (req.url.startsWith("/api/")) {

    const target =
      `${API_URL}${req.url.replace("/api", "")}`;

    const url =
      new URL(target);

    const client =
      url.protocol === "https:"
        ? https
        : http;

    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: req.method,
      headers: req.headers
    };

    const proxyReq =
      client.request(
        options,
        (proxyRes) => {

          res.writeHead(
            proxyRes.statusCode,
            proxyRes.headers
          );

          proxyRes.pipe(res);

        }
      );

    proxyReq.on("error", (err) => {

      res.writeHead(502, {
        "Content-Type":
          "application/json"
      });

      res.end(
        JSON.stringify({
          error: "API unavailable",
          details: err.message
        })
      );

    });

    req.pipe(proxyReq);

    return;
  }

  const html =
    fs.readFileSync(
      path.join(
        __dirname,
        "index.html"
      ),
      "utf8"
    );

  res.writeHead(
    200,
    {
      "Content-Type":
        "text/html"
    }
  );

  res.end(html);

});

server.listen(
  PORT,
  () => {
    console.log(
      `Web server running on :${PORT}`
    );
  }
);
