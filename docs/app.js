/*
 * Landing page de ponte -> grupo do WhatsApp.
 * 1. Detecta a origem do visitante (meta / tiktok / outros)
 * 2. Carrega Meta Pixel e TikTok Pixel (se configurados)
 * 3. No clique: registra no webhook do Make, dispara evento nos pixels e redireciona
 */
(function () {
  "use strict";

  var C = window.LP_CONFIG || {};
  var params = new URLSearchParams(location.search);

  // ---------- Origem ----------
  function detectarOrigem() {
    var src = (params.get("utm_source") || params.get("s") || "").toLowerCase();
    var ref = (document.referrer || "").toLowerCase();
    var origem = "direto";

    if (/^(fb|facebook|ig|instagram|meta)/.test(src)) origem = "meta";
    else if (/^(tt|tiktok)/.test(src)) origem = "tiktok";
    else if (src) origem = src;
    else if (params.has("fbclid") || /facebook\.|instagram\.|fb\.me/.test(ref)) origem = "meta";
    else if (params.has("ttclid") || /tiktok\./.test(ref)) origem = "tiktok";

    return {
      src: origem,
      med: params.get("utm_medium") || (params.has("fbclid") || params.has("ttclid") ? "desconhecido" : ""),
      camp: params.get("utm_campaign") || "",
      cont: params.get("utm_content") || "",
      fbclid: params.get("fbclid") || "",
      ttclid: params.get("ttclid") || "",
      ref: ref ? ref.split("/")[2] || "" : ""
    };
  }

  // Guarda a origem da primeira página vista na sessão (ex.: visitante abre a política e volta).
  var origem;
  try {
    origem = JSON.parse(sessionStorage.getItem("lp_origem") || "null");
  } catch (e) { origem = null; }
  if (!origem || location.search) {
    origem = detectarOrigem();
    try { sessionStorage.setItem("lp_origem", JSON.stringify(origem)); } catch (e) { /* ignorar */ }
  }

  // ---------- Pixels ----------
  if (C.metaPixelId) {
    !function (f, b, e, v, n, t, s) {
      if (f.fbq) return; n = f.fbq = function () {
        n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
      };
      if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = "2.0"; n.queue = [];
      t = b.createElement(e); t.async = !0; t.src = v;
      s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
    }(window, document, "script", "https://connect.facebook.net/en_US/fbevents.js");
    window.fbq("init", C.metaPixelId);
    window.fbq("track", "PageView");
  }

  if (C.tiktokPixelId) {
    !function (w, d, t) {
      w.TiktokAnalyticsObject = t;
      var ttq = w[t] = w[t] || [];
      ttq.methods = ["page", "track", "identify", "instances", "debug", "on", "off", "once", "ready",
        "alias", "group", "enableCookie", "disableCookie", "holdConsent", "revokeConsent", "grantConsent"];
      ttq.setAndDefer = function (t, e) {
        t[e] = function () { t.push([e].concat(Array.prototype.slice.call(arguments, 0))); };
      };
      for (var i = 0; i < ttq.methods.length; i++) ttq.setAndDefer(ttq, ttq.methods[i]);
      ttq.instance = function (t) {
        for (var e = ttq._i[t] || [], n = 0; n < ttq.methods.length; n++) ttq.setAndDefer(e, ttq.methods[n]);
        return e;
      };
      ttq.load = function (e, n) {
        var r = "https://analytics.tiktok.com/i18n/pixel/events.js";
        ttq._i = ttq._i || {}; ttq._i[e] = []; ttq._i[e]._u = r;
        ttq._t = ttq._t || {}; ttq._t[e] = +new Date;
        ttq._o = ttq._o || {}; ttq._o[e] = n || {};
        var s = d.createElement("script"); s.type = "text/javascript"; s.async = !0;
        s.src = r + "?sdkid=" + e + "&lib=" + t;
        var x = d.getElementsByTagName("script")[0]; x.parentNode.insertBefore(s, x);
      };
      ttq.load(C.tiktokPixelId);
      ttq.page();
    }(window, document, "ttq");
  }

  // ---------- Clique ----------
  var grupos = C.gruposWhatsApp || [];
  var indiceGrupo = Math.min(C.grupoAtivo || 0, Math.max(grupos.length - 1, 0));
  var linkGrupo = grupos[indiceGrupo] || "";
  var cta = document.getElementById("cta");
  if (linkGrupo) cta.href = linkGrupo;

  function novoId() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  }

  function registrarNoMake(eventId) {
    if (!C.makeWebhookUrl) return;
    var dados = new URLSearchParams({
      ts: new Date().toISOString(),
      src: origem.src,
      med: origem.med,
      camp: origem.camp,
      cont: origem.cont,
      fbclid: origem.fbclid,
      ttclid: origem.ttclid,
      ref: origem.ref,
      grp: String(indiceGrupo),
      eid: eventId
    });
    // sendBeacon sobrevive ao redirecionamento; form-urlencoded evita bloqueio de CORS.
    if (!(navigator.sendBeacon && navigator.sendBeacon(C.makeWebhookUrl, dados))) {
      fetch(C.makeWebhookUrl, { method: "POST", body: dados, mode: "no-cors", keepalive: true })
        .catch(function () { /* nunca bloquear o visitante */ });
    }
  }

  function dispararPixels(eventId) {
    var props = { content_name: "grupo_whatsapp", content_category: origem.src };
    if (window.fbq) window.fbq("track", "Lead", props, { eventID: eventId });
    if (window.ttq) window.ttq.track("Contact", props, { event_id: eventId });
  }

  var clicou = false;
  cta.addEventListener("click", function (ev) {
    if (!linkGrupo) return;
    ev.preventDefault();
    if (clicou) return;
    clicou = true;

    var eventId = novoId();
    registrarNoMake(eventId);
    dispararPixels(eventId);

    // Pequena espera para os pixels enviarem o evento antes de sair da página.
    setTimeout(function () { location.href = linkGrupo; }, C.redirectDelayMs || 350);
  });
})();
