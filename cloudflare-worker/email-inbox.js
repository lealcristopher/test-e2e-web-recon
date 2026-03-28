export default {
  // Handle HTTP requests (API to query emails)
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Auth check
    const authHeader = request.headers.get("X-API-Key");
    if (authHeader !== env.API_KEY) {
      return new Response("Unauthorized", { status: 401 });
    }

    // GET /messages — list all emails
    if (request.method === "GET" && path === "/messages") {
      const list = await env.EMAIL_INBOX.list();
      const messages = [];
      for (const key of list.keys) {
        const value = await env.EMAIL_INBOX.get(key.name);
        if (value) messages.push(JSON.parse(value));
      }
      messages.sort((a, b) => new Date(b.received_at) - new Date(a.received_at));
      return Response.json(messages);
    }

    // GET /messages/:id — get single email
    if (request.method === "GET" && path.startsWith("/messages/")) {
      const id = path.replace("/messages/", "");
      const value = await env.EMAIL_INBOX.get(id);
      if (!value) return new Response("Not found", { status: 404 });
      return Response.json(JSON.parse(value));
    }

    // DELETE /messages — clear inbox
    if (request.method === "DELETE" && path === "/messages") {
      const list = await env.EMAIL_INBOX.list();
      for (const key of list.keys) {
        await env.EMAIL_INBOX.delete(key.name);
      }
      return Response.json({ deleted: list.keys.length });
    }

    // DELETE /messages/:id — delete single email
    if (request.method === "DELETE" && path.startsWith("/messages/")) {
      const id = path.replace("/messages/", "");
      await env.EMAIL_INBOX.delete(id);
      return new Response(null, { status: 204 });
    }

    return new Response("Not found", { status: 404 });
  },

  // Handle incoming emails
  async email(message, env) {
    const id = crypto.randomUUID();

    // Read raw email body
    const rawEmail = await new Response(message.raw).text();

    // Extract HTML body from MIME
    let htmlBody = "";
    let textBody = "";

    const htmlMatch = rawEmail.match(/Content-Type: text\/html[^\r\n]*\r?\n(?:[^\r\n]*\r?\n)*\r?\n([\s\S]*?)(?:\r?\n--|\r?\n\r?\n--)/i);
    if (htmlMatch) htmlBody = htmlMatch[1].trim();

    const textMatch = rawEmail.match(/Content-Type: text\/plain[^\r\n]*\r?\n(?:[^\r\n]*\r?\n)*\r?\n([\s\S]*?)(?:\r?\n--)/i);
    if (textMatch) textBody = textMatch[1].trim();

    // Fallback: use raw if no MIME parts found
    if (!htmlBody && !textBody) textBody = rawEmail;

    const record = {
      id,
      from: message.from,
      to: message.to,
      subject: message.headers.get("subject") || "",
      received_at: new Date().toISOString(),
      html: htmlBody,
      text: textBody,
      raw: rawEmail,
    };

    // Store with 24h TTL
    await env.EMAIL_INBOX.put(id, JSON.stringify(record), { expirationTtl: 86400 });
  },
};
