/*
 * The in-iframe marking bridge — PREVIEW MODE ONLY.
 *
 * Gate 2's design window embeds the running preview in an iframe. The preview
 * is served from its own origin (its own sandbox, its own port), so the parent
 * cannot reach into its DOM at all: `iframe.contentDocument` is null and
 * `elementFromPoint` is unreachable. Everything the shell knows about what the
 * user marked has to be *sent out* from inside.
 *
 * That is what this file is. It runs inside the preview, captures clicks on
 * instrumented elements, draws a marker, and postMessages the identity of the
 * element to the parent.
 *
 * Two rules it must not break:
 *
 * 1. **It never ships.** The layout includes it only when SCIO_PREVIEW_MODE is
 *    set. The app the user receives has no bridge, no listener and no marker.
 * 2. **It resolves nothing.** It reports the element under the pointer and,
 *    separately, the nearest instrumented ancestor — and never substitutes one
 *    for the other. The sandbox-marking spike proved why: a click that fell
 *    through to an ancestor resolved confidently to the wrong package, and a
 *    directed change would have rewritten the app shell. Deciding is the
 *    resolver's job (core/resolver.py), which is strict about exactly this.
 */
(function () {
  "use strict";

  var ID = "data-scio-id";
  var PKG = "data-scio-package";
  // Who we are allowed to talk to. Injected by the server that serves the
  // preview; postMessage to "*" would broadcast the app's structure to any page
  // that managed to frame it.
  var SHELL_ORIGIN = window.__SCIO_SHELL_ORIGIN__ || "";

  if (window.top === window.self) {
    // Not embedded — nothing to talk to. Marking is a design-window feature.
    return;
  }

  var markers = [];

  function styleOnce() {
    if (document.getElementById("scio-bridge-style")) return;
    var style = document.createElement("style");
    style.id = "scio-bridge-style";
    style.textContent =
      ".scio-mark{position:absolute;border:2px solid #0d9488;border-radius:3px;" +
      "pointer-events:none;z-index:2147483647;box-shadow:0 0 0 9999px rgba(13,148,136,.06)}" +
      ".scio-mark-tag{position:absolute;top:-20px;left:-2px;background:#0d9488;color:#fff;" +
      "font:11px/1.5 ui-monospace,monospace;padding:0 5px;border-radius:3px;white-space:nowrap}" +
      ".scio-armed{cursor:crosshair}";
    document.head.appendChild(style);
  }

  function draw(element, label) {
    styleOnce();
    var box = element.getBoundingClientRect();
    var mark = document.createElement("div");
    mark.className = "scio-mark";
    mark.style.left = box.left + window.scrollX + "px";
    mark.style.top = box.top + window.scrollY + "px";
    mark.style.width = box.width + "px";
    mark.style.height = box.height + "px";
    var tag = document.createElement("div");
    tag.className = "scio-mark-tag";
    tag.textContent = label;
    mark.appendChild(tag);
    document.body.appendChild(mark);
    markers.push(mark);
  }

  function clearMarks() {
    markers.forEach(function (m) {
      m.remove();
    });
    markers = [];
  }

  /**
   * What the browser found, reported without interpretation.
   *
   * Deliberately the same shape as core/resolver.ElementHit, so the parent can
   * hand it straight to the strict resolver. `ancestor_*` is evidence for an
   * error message, never a fallback answer.
   */
  function describe(node) {
    var ancestor = node.parentElement;
    var distance = 1;
    while (ancestor && !ancestor.getAttribute(ID)) {
      ancestor = ancestor.parentElement;
      distance += 1;
    }
    return {
      scio_id: node.getAttribute(ID),
      scio_package: node.getAttribute(PKG),
      tag: node.tagName.toLowerCase(),
      text: (node.innerText || "").trim().slice(0, 80),
      ancestor_id: ancestor ? ancestor.getAttribute(ID) : null,
      ancestor_package: ancestor ? ancestor.getAttribute(PKG) : null,
      ancestor_distance: ancestor ? distance : 0,
    };
  }

  function send(type, payload) {
    if (!SHELL_ORIGIN) return;
    window.parent.postMessage(Object.assign({ source: "scio-preview", type: type }, payload), SHELL_ORIGIN);
  }

  var armed = false;

  function onClick(event) {
    if (!armed) return;
    // The preview is a working app: submitting the form while marking it would
    // navigate away from the thing being marked.
    event.preventDefault();
    event.stopPropagation();

    var node = document.elementFromPoint(event.clientX, event.clientY);
    if (!node) return;
    var hit = describe(node);

    draw(node, hit.scio_id || "no " + ID);
    send("marked", {
      hit: hit,
      // Viewport coordinates, and the scroll they were taken at. The parent
      // cannot compute these itself — it has no access to this document.
      coords: {
        x: Math.round(event.clientX),
        y: Math.round(event.clientY),
        scroll_y: Math.round(window.scrollY),
      },
      route: window.location.pathname,
    });
  }

  window.addEventListener("message", function (event) {
    if (SHELL_ORIGIN && event.origin !== SHELL_ORIGIN) return;
    var data = event.data || {};
    if (data.source !== "scio-shell") return;
    if (data.type === "arm") {
      armed = !!data.on;
      document.documentElement.classList.toggle("scio-armed", armed);
    }
    if (data.type === "clear") clearMarks();
  });

  document.addEventListener("click", onClick, true);

  // Tell the shell we are alive, with the ids on this page. The shell uses it to
  // show that the bridge — not DOM access — is what made marking possible.
  send("ready", {
    route: window.location.pathname,
    ids: Array.prototype.slice
      .call(document.querySelectorAll("[" + ID + "]"))
      .map(function (el) {
        return el.getAttribute(ID);
      }),
  });
})();
