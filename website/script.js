// TeaSpoon landing page — count-up stats + scroll reveal. No dependencies.
(function () {
  "use strict";

  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // --- Scroll reveal -------------------------------------------------------
  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !prefersReduced) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            if (entry.target.querySelector("[data-count]")) countUp(entry.target);
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.18 }
    );
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("in"));
    document.querySelectorAll("[data-count]").forEach(setFinal);
  }

  // --- Animated count-up for the hero stats --------------------------------
  function countUp(scope) {
    scope.querySelectorAll("[data-count]").forEach((el) => {
      const target = Number(el.getAttribute("data-count"));
      const prefix = el.getAttribute("data-prefix") || "";
      const suffix = el.getAttribute("data-suffix") || "";
      const duration = 1100;
      const start = performance.now();

      function frame(now) {
        const t = Math.min(1, (now - start) / duration);
        const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
        const value = Math.round(target * eased);
        el.textContent = prefix + value.toLocaleString("en-IN") + suffix;
        if (t < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    });
  }

  function setFinal(el) {
    const target = Number(el.getAttribute("data-count"));
    const prefix = el.getAttribute("data-prefix") || "";
    const suffix = el.getAttribute("data-suffix") || "";
    el.textContent = prefix + target.toLocaleString("en-IN") + suffix;
  }
})();
