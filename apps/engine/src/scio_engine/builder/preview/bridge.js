/*
 * The marking bridge — PREVIEW BUILDS ONLY.
 *
 * Gate 2's design window embeds the running app in an iframe. The app is served
 * from its own sandbox on its own origin, so the window cannot reach into its
 * DOM at all — `contentDocument` throws. Everything the window knows about what
 * the user marked has to be sent out from inside. That is this file.
 *
 * Proven in spikes/design-marking (see its FINDINGS.md). Three rules come from
 * there, and none of them are negotiable:
 *
 * 1. **It never ships.** next.config.js adds this to the client bundle only when
 *    SCIO_PREVIEW_MODE is set. A delivery build does not register the entry, so
 *    the code is not in the bundle at all — not disabled, absent.
 *
 * 2. **It stays dumb.** It reports the element under the pointer AND, separately,
 *    the nearest instrumented ancestor, and never substitutes one for the other.
 *    Deciding is `core/resolver.resolve_marking`'s job, and it refuses by name.
 *    The sandbox-marking spike (B039) showed what the alternative costs: a click
 *    that fell through to an ancestor resolved confidently to the wrong package,
 *    and a directed change would have rewritten the app shell.
 *
 * 3. **Origins are pinned in both directions.** It posts only to the shell's
 *    origin, and ignores anything that did not come from it. A wildcard here
 *    would hand the app's structure to any page that managed to frame it.
 */
(function () {
  "use strict";

  var ID = "data-scio-id";
  var PKG = "data-scio-package";
  var SHELL_ORIGIN = process.env.NEXT_PUBLIC_SCIO_SHELL_ORIGIN || "";

  if (typeof window === "undefined") return;
  if (window.top === window.self) {
    // Not embedded. Marking is a design-window feature and there is nobody to
    // talk to — so the app behaves exactly as delivered.
    return;
  }
  if (window.__scioBridge) return;
  window.__scioBridge = true;

  var armed = false;
  var markers = [];

  function styleOnce() {
    if (document.getElementById("scio-bridge-style")) return;
    var style = document.createElement("style");
    style.id = "scio-bridge-style";
    style.textContent =
      ".scio-mark{position:absolute;border:2px solid #0d9488;border-radius:3px;" +
      "pointer-events:none;z-index:2147483647}" +
      ".scio-mark-tag{position:absolute;left:-2px;background:#0d9488;color:#fff;" +
      "font:11px/1.5 ui-monospace,monospace;padding:0 5px;border-radius:3px;white-space:nowrap}" +
      ".scio-armed,.scio-armed *{cursor:crosshair!important}";
    document.head.appendChild(style);
  }

  /**
   * The marker is drawn HERE, not by the parent.
   *
   * The parent cannot: these coordinates are in this document's viewport with
   * this document's scroll, and it can read neither. Anything it painted on top
   * of the iframe would drift the moment someone scrolled.
   */
  function draw(element, label, index) {
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
    // Above the box, unless there is no room — labels on adjacent elements
    // otherwise land on top of each other.
    tag.style.top = box.top > 22 ? "-20px" : box.height + 2 + "px";
    tag.textContent = (index + 1) + " · " + label;
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

  /** What is there, reported without interpretation. Shape: core.resolver.ElementHit. */
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
    var message = { source: "scio-preview", type: type };
    for (var key in payload) {
      if (Object.prototype.hasOwnProperty.call(payload, key)) message[key] = payload[key];
    }
    window.parent.postMessage(message, SHELL_ORIGIN);
  }

  function onClick(event) {
    if (!armed) return;
    // The preview is a working app. Marking the submit button must not submit
    // the form and navigate away from the thing being marked.
    event.preventDefault();
    event.stopPropagation();

    var node = document.elementFromPoint(event.clientX, event.clientY);
    if (!node) return;
    var hit = describe(node);

    draw(node, hit.scio_id || "not addressable", markers.length);
    send("marked", {
      hit: hit,
      coords: {
        x: Math.round(event.clientX),
        y: Math.round(event.clientY),
        scroll_y: Math.round(window.scrollY),
      },
      route: window.location.pathname,
    });
  }

  // Submitting, navigating and typing are all "the app working". While armed,
  // none of them should happen — the user is pointing, not using.
  function suppress(event) {
    if (armed) {
      event.preventDefault();
      event.stopPropagation();
    }
  }

  window.addEventListener("message", function (event) {
    if (!SHELL_ORIGIN || event.origin !== SHELL_ORIGIN) return;
    var data = event.data || {};
    if (data.source !== "scio-shell") return;
    if (data.type === "arm") {
      armed = !!data.on;
      document.documentElement.classList.toggle("scio-armed", armed);
    }
    if (data.type === "clear") clearMarks();
    if (data.type === "ping") send("ready", inventory());
  });

  function inventory() {
    return {
      route: window.location.pathname,
      ids: Array.prototype.slice
        .call(document.querySelectorAll("[" + ID + "]"))
        .map(function (el) {
          return el.getAttribute(ID);
        }),
    };
  }

  document.addEventListener("click", onClick, true);
  document.addEventListener("submit", suppress, true);
  document.addEventListener("keydown", suppress, true);

  // Announce, so the window knows the bridge — not DOM access — is what makes
  // marking possible here, and which ids this route actually has.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      send("ready", inventory());
    });
  } else {
    send("ready", inventory());
  }
})();
