(function () {
  const STYLES = window.DRAFTELIER_STYLES || [];
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const pad = (n) => String(n).padStart(2, "0");

  /* ───────── Make.com integration ─────────
   * Paste your webhook URL here after importing make/draftelier-gemini-blueprint.json
   * and activating the scenario. Leave empty to keep the local CSS-filter preview.
   */
  const MAKE_WEBHOOK_URL = window.DRAFTELIER_WEBHOOK || "https://hook.us2.make.com/jl3uv0zj2wpcr51fofmqafdgl8a8nvbo";
  const GEMINI_MODEL_PRIMARY = "gemini-3-pro-image-preview";
  const GEMINI_MODEL_FALLBACK = "gemini-2.5-flash-image";

  const ASPECTS = {
    portrait:  { w: 1440, h: 1800 },
    landscape: { w: 2000, h: 1400 }
  };

  /* ───────── i18n ───────── */
  const I18N = {
    zh: {
      "nav.city": "上海 · 中国",
      "nav.est": "创办于 MMXXVI",
      "nav.atelier": "工坊",
      "nav.archive": "档案",
      "nav.method": "方法",
      "hero.pre": "渲染语言 · 第 一 辑",
      "hero.volume": "Vol. MMXXVI · 十六种手稿语汇",
      "hero.tag.1": "一件衣服已被设计。",
      "hero.tag.2": "改变的，是描绘它的那支笔。",
      "hero.cta": "进入工坊",
      "atelier.kicker": "工坊 · Atelier",
      "atelier.title": "上传一张照片，选择一种语言。",
      "atelier.lede": "你的轮廓保持不变——改变的只是介质、笔触与留白。所有合成在浏览器本地完成，不上传任何服务器。",
      "atelier.upload": "上传照片",
      "atelier.clear": "清空",
      "atelier.dz.title": "将照片拖拽到此处",
      "atelier.dz.sub": "或点击选择 · JPG / PNG",
      "atelier.legal": "仅限本人或已获授权的照片；请勿上传秀场、杂志、明星截图等版权素材。",
      "atelier.pick": "选择渲染语言",
      "atelier.preview": "编辑海报 · 即时预览",
      "atelier.download": "下载 PNG ↓",
      "atelier.ph.main": "上传照片 & 选择一种风格",
      "atelier.ph.sub": "此处将生成一张编辑式海报",
      "arch.kicker": "档案 · Archive",
      "arch.title": "十六只手，一种纪律。",
      "arch.lede": "每条语言由「介质 · 笔触 · 氛围」三元组定义。点击卡片，查看家族谱系、训练 token 与研究笔记。",
      "arch.filter.all": "全部",
      "arch.filter.ready": "已就绪",
      "arch.filter.preview": "预览中",
      "method.kicker": "方法论 · Method",
      "method.title": "只换笔，不改形。",
      "method.1.h": "先有照片",
      "method.1.p": "保留原始廓形、比例与姿态——档案不做造型改造，只替换描绘它的那支笔。",
      "method.2.h": "语法三元组",
      "method.2.p": "介质决定质感，笔触决定节奏，氛围决定页面留白。三者共同定义一条语言。",
      "method.3.h": "Token 与 LoRA",
      "method.3.p": "每条语言对应一个 token 与一组 LoRA 权重，作为可反复调用的视觉透镜。",
      "method.4.h": "谱系，非 Logo",
      "method.4.p": "以家族谱系方式致敬设计师，不复制 logo、品牌名或原样作品。",
      "footer.c": "© %Y Draftelier 渲染语言档案",
      "footer.edition": "Vol. 01 — 静态版",
      "modal.close": "关闭 ✕",
      // modal labels
      "m.lineage": "家族谱系",
      "m.medium": "介质 · Medium",
      "m.strokes": "笔触 · Strokes",
      "m.vibe": "氛围 · Vibe",
      "m.notes": "研究笔记",
      "m.token": "训练 Token",
      "m.status": "状态",
      "m.ready": "LoRA 就绪",
      "m.preview": "预览中",
      "m.open": "在工坊试用此语言 ⟶",
      // card foot
      "c.open": "展开 ↗"
    },
    en: {
      "nav.city": "Shanghai · China",
      "nav.est": "Est. MMXXVI",
      "nav.atelier": "Atelier",
      "nav.archive": "Archive",
      "nav.method": "Method",
      "hero.pre": "Rendering Languages · Vol. I",
      "hero.volume": "Vol. MMXXVI · Sixteen Manuscript Hands",
      "hero.tag.1": "A garment is already designed.",
      "hero.tag.2": "What changes is the hand that draws it.",
      "hero.cta": "Enter the Atelier",
      "atelier.kicker": "Atelier · 工坊",
      "atelier.title": "Upload a photo. Choose a language.",
      "atelier.lede": "Your silhouette stays untouched — only the medium, stroke and silence around it change. Everything renders locally in your browser; nothing is uploaded.",
      "atelier.upload": "Upload",
      "atelier.clear": "Clear",
      "atelier.dz.title": "Drop a photo here",
      "atelier.dz.sub": "or click to select · JPG / PNG",
      "atelier.legal": "Only your own or fully licensed photos. Do not upload runway, magazine, or celebrity imagery.",
      "atelier.pick": "Choose a Rendering Language",
      "atelier.preview": "Editorial Poster · Live Preview",
      "atelier.download": "Download PNG ↓",
      "atelier.ph.main": "Upload a photo & pick a style",
      "atelier.ph.sub": "An editorial poster will render here",
      "arch.kicker": "Archive · 档案",
      "arch.title": "Sixteen hands, one discipline.",
      "arch.lede": "Each language is defined by a triad — Medium · Strokes · Vibe. Click a card to open its lineage, training token and research notes.",
      "arch.filter.all": "All",
      "arch.filter.ready": "LoRA Ready",
      "arch.filter.preview": "Preview",
      "method.kicker": "Method · 方法论",
      "method.title": "A rendering, not a redesign.",
      "method.1.h": "Photo first",
      "method.1.p": "The original silhouette, proportion and pose are preserved. We never restyle — we replace only the hand that draws it.",
      "method.2.h": "Grammar triad",
      "method.2.p": "Medium sets the texture, strokes set the rhythm, vibe sets the silence. Together they define one language.",
      "method.3.h": "Token & LoRA",
      "method.3.p": "Each language is bound to a training token and a LoRA weight — a callable visual lens.",
      "method.4.h": "Lineage, not logo",
      "method.4.p": "We honour designers as lineages. We never copy logos, brand marks or actual works.",
      "footer.c": "© %Y Draftelier Rendering-Language Archive",
      "footer.edition": "Vol. 01 — Static Edition",
      "modal.close": "Close ✕",
      "m.lineage": "Lineage",
      "m.medium": "Medium",
      "m.strokes": "Strokes",
      "m.vibe": "Vibe",
      "m.notes": "Research Notes",
      "m.token": "Training Token",
      "m.status": "Status",
      "m.ready": "LoRA Ready",
      "m.preview": "Preview",
      "m.open": "Try this language in Studio ⟶",
      "c.open": "Open ↗"
    }
  };

  const state = {
    lang: "zh",
    selectedStyleId: STYLES[0]?.id || null,
    imageBitmap: null,
    imageDataUrl: null,
    aiBitmap: null,
    aspect: "auto",
    currentFilter: "all"
  };

  const t = (key) => (I18N[state.lang] && I18N[state.lang][key]) || key;

  function applyI18n() {
    document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
    document.documentElement.dataset.lang = state.lang;
    $$("[data-i18n]").forEach((el) => {
      const key = el.dataset.i18n;
      const val = t(key);
      // footer.c contains a span#year placeholder
      if (key === "footer.c") {
        el.innerHTML = val.replace("%Y", `<span id="year">${new Date().getFullYear()}</span>`);
      } else {
        el.textContent = val;
      }
    });
    // re-render language-dependent content
    renderStyleRail();
    updateCurrentLabel();
    // if modal is open, refresh
    if ($("#modal").classList.contains("open") && state.openModalId) {
      openModal(state.openModalId);
    }
    renderPoster();
  }

  function setLang(lang) {
    state.lang = lang;
    $$(".lang-toggle button").forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
    applyI18n();
  }

  /* ───────── MARQUEE GALLERY ───────── */
  function buildMqCard(item, n) {
    const frame = item.frame || "bracket";
    const num = "№ " + String(n).padStart(2, "0");
    const isMedia = item.src && /\.(jpe?g|png|webp|avif|gif|svg)(\?.*)?$/i.test(item.src);
    const inner = isMedia
      ? `<img src="${item.src}" alt="${item.label || num}" loading="lazy" />`
      : `<div class="mq-placeholder">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="1" width="26" height="26" stroke="currentColor" stroke-width="1"/><path d="M8 20 L14 8 L20 20" stroke="currentColor" stroke-width="1" fill="none"/></svg>
          <span>${num}</span>
         </div>`;
    const trText = frame === "editorial" ? num : "";
    return `<div class="mq-card" data-frame="${frame}">
      ${inner}
      <div class="mq-frame" aria-hidden="true">
        <span class="mc-tl"></span>
        <span class="mc-tr">${trText}</span>
        <span class="mc-bl"></span>
        <span class="mc-br"></span>
      </div>
      ${item.label ? `<p class="mq-label">${item.label}</p>` : ""}
    </div>`;
  }

  function initMarquee() {
    const track = $("#mq-track");
    if (!track) return;
    const items = (window.DRAFTELIER_GALLERY || []).filter(Boolean);
    if (!items.length) return;
    const doubled = [...items, ...items];
    track.innerHTML = doubled.map((item, i) => buildMqCard(item, (i % items.length) + 1)).join("");
  }

  /* ───────── STYLE RAIL ───────── */
  function renderStyleRail() {
    const rail = $("#style-rail");
    rail.innerHTML = STYLES.map((s, i) => {
      const title = state.lang === "zh" ? s.cnName : s.name;
      const sub   = state.lang === "zh" ? s.name : s.cnName;
      return `
      <button type="button" class="style-chip${s.id === state.selectedStyleId ? " active" : ""}" data-id="${s.id}">
        <span class="chip-num">№ ${pad(i + 1)}</span>
        <span class="chip-title">${title}</span>
        <span class="chip-cn">${sub}</span>
        <span class="chip-meta">${s.loraReady ? t("m.ready") : t("m.preview")}</span>
      </button>`;
    }).join("");
    $$(".style-chip", rail).forEach((el) => {
      el.addEventListener("click", () => selectStyle(el.dataset.id));
    });
  }

  function selectStyle(id) {
    state.selectedStyleId = id;
    $$(".style-chip").forEach((el) => el.classList.toggle("active", el.dataset.id === id));
    updateCurrentLabel();
    renderPoster();
  }

  function updateCurrentLabel() {
    const s = STYLES.find((x) => x.id === state.selectedStyleId);
    const el = $("#current-style-label");
    if (!el) return;
    if (!s) { el.textContent = "—"; return; }
    el.textContent = state.lang === "zh" ? s.cnName : s.name;
  }

  /* ───────── DROPZONE ───────── */
  function setupDropzone() {
    const dz = $("#dropzone");
    const input = $("#file-input");
    const preview = $("#dz-preview");
    const clear = $("#dz-clear");

    const handleFiles = (files) => {
      if (!files || !files[0]) return;
      const file = files[0];
      if (!file.type.startsWith("image/")) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        const dataUrl = e.target.result;
        preview.src = dataUrl;
        dz.classList.add("has-image");
        clear.hidden = false;
        const img = new Image();
        img.onload = () => {
          state.imageBitmap = img;
          state.imageDataUrl = dataUrl;
          state.aiBitmap = null;
          renderPoster();
        };
        img.src = dataUrl;
      };
      reader.readAsDataURL(file);
    };

    input.addEventListener("change", (e) => handleFiles(e.target.files));
    ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => {
      e.preventDefault(); dz.classList.add("drag");
    }));
    ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => {
      e.preventDefault(); dz.classList.remove("drag");
    }));
    dz.addEventListener("drop", (e) => {
      e.preventDefault();
      if (e.dataTransfer?.files?.length) handleFiles(e.dataTransfer.files);
    });

    clear.addEventListener("click", (e) => {
      e.preventDefault(); e.stopPropagation();
      state.imageBitmap = null;
      state.imageDataUrl = null;
      state.aiBitmap = null;
      preview.src = ""; input.value = "";
      dz.classList.remove("has-image");
      clear.hidden = true;
      renderPoster();
    });
  }

  /* ───────── POSTER ───────── */
  const STYLE_FILTERS = {
    dior: "contrast(1.02) saturate(0.78) brightness(1.04) sepia(0.18)",
    balenciaga: "grayscale(0.65) contrast(1.1) brightness(1.02)",
    schiaparelli: "contrast(1.2) saturate(1.25) brightness(0.96) hue-rotate(-8deg)",
    chanel: "grayscale(0.2) contrast(1.22) brightness(1.04)",
    mugler: "contrast(1.35) saturate(1.1) brightness(0.9)",
    galliano: "contrast(1.08) saturate(1.2) sepia(0.22)",
    gaultier: "contrast(1.25) saturate(0.95)",
    westwood: "contrast(1.12) saturate(0.85) sepia(0.1)",
    maison_margiela: "grayscale(0.9) contrast(0.88) brightness(1.08)",
    iris_van_herpen: "contrast(1.15) saturate(0.6) brightness(1.05) hue-rotate(180deg)",
    issey_miyake: "contrast(1.05) saturate(0.7) brightness(1.1)",
    courreges: "grayscale(0.3) contrast(1.15) brightness(1.06)",
    rabanne: "grayscale(0.5) contrast(1.3) brightness(0.98)",
    gucci: "contrast(1.08) saturate(1.4) sepia(0.15)",
    mcqueen: "grayscale(0.75) contrast(1.3) brightness(0.88)",
    ysl: "grayscale(0.4) contrast(1.2) brightness(1.02)"
  };

  function resolveAspect() {
    if (state.aspect === "portrait" || state.aspect === "landscape") return ASPECTS[state.aspect];
    const img = state.aiBitmap || state.imageBitmap;
    if (img && img.naturalWidth > img.naturalHeight) return ASPECTS.landscape;
    return ASPECTS.portrait;
  }

  function renderPoster() {
    const canvas = $("#poster-canvas");
    const placeholder = $("#poster-placeholder");
    const dl = $("#download-poster");
    const share = $("#share-poster");
    const genBtn = $("#generate-ai");
    const style = STYLES.find((s) => s.id === state.selectedStyleId);

    const dims = resolveAspect();
    if (canvas.width !== dims.w || canvas.height !== dims.h) {
      canvas.width = dims.w;
      canvas.height = dims.h;
    }

    if (!state.imageBitmap || !style) {
      placeholder.classList.remove("hidden");
      dl.hidden = true;
      if (share) share.hidden = true;
      if (genBtn) {
        genBtn.disabled = true;
        genBtn.title = state.lang === "zh" ? "先上传图片再进行 AI 绘图" : "Upload an image before AI drawing";
      }
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }
    placeholder.classList.add("hidden");
    if (genBtn) {
      genBtn.disabled = !MAKE_WEBHOOK_URL;
      genBtn.title = MAKE_WEBHOOK_URL
        ? (state.lang === "zh" ? "点击使用 AI 绘图" : "Click to generate with AI")
        : (state.lang === "zh" ? "请先配置 Make webhook" : "Configure Make webhook first");
    }

    const W = canvas.width, H = canvas.height;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, W, H);

    ctx.fillStyle = "#f2ecdc";
    ctx.fillRect(0, 0, W, H);
    paintGrain(ctx, W, H);

    const marginOuter = Math.round(W * 0.04);
    const marginInner = Math.round(W * 0.056);
    ctx.strokeStyle = "#0b0b0b";
    ctx.lineWidth = 3; ctx.strokeRect(marginOuter, marginOuter, W - marginOuter * 2, H - marginOuter * 2);
    ctx.lineWidth = 1; ctx.strokeRect(marginInner, marginInner, W - marginInner * 2, H - marginInner * 2);

    const headerY = Math.round(H * 0.065);
    ctx.fillStyle = "#0b0b0b";
    ctx.font = `500 ${Math.round(W * 0.014)}px "JetBrains Mono", monospace`;
    ctx.textBaseline = "alphabetic";
    ctx.textAlign = "left";
    ctx.fillText("DRAFTELIER", marginInner + 24, headerY);
    ctx.textAlign = "right";
    ctx.fillText("ATELIER · EDITION № " + pad(STYLES.indexOf(style) + 1), W - marginInner - 24, headerY);

    ctx.strokeStyle = "#a67a3f";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(marginInner + 24, headerY + 20);
    ctx.lineTo(W - marginInner - 24, headerY + 20);
    ctx.stroke();

    const isLandscape = W > H;
    let frameX, frameY, frameW, frameH, capX, capY, capW;
    if (isLandscape) {
      frameX = marginInner + 24;
      frameY = headerY + 40;
      frameW = Math.round(W * 0.55);
      frameH = H - frameY - Math.round(H * 0.12);
      capX = frameX + frameW + Math.round(W * 0.025);
      capY = frameY;
      capW = W - capX - marginInner - 24;
    } else {
      frameX = marginInner + 24;
      frameY = headerY + 40;
      frameW = W - (marginInner + 24) * 2;
      frameH = Math.round(H * 0.58);
      capX = frameX;
      capY = frameY + frameH + Math.round(H * 0.035);
      capW = frameW;
    }

    ctx.fillStyle = "#e9e2d0";
    ctx.fillRect(frameX, frameY, frameW, frameH);

    const img = state.aiBitmap || state.imageBitmap;
    const scale = Math.min(frameW / img.naturalWidth, frameH / img.naturalHeight);
    const dw = img.naturalWidth * scale;
    const dh = img.naturalHeight * scale;
    const dx = frameX + (frameW - dw) / 2;
    const dy = frameY + (frameH - dh) / 2;

    ctx.save();
    if (!state.aiBitmap) {
      ctx.filter = STYLE_FILTERS[style.id] || "none";
    }
    ctx.drawImage(img, dx, dy, dw, dh);
    ctx.restore();

    ctx.strokeStyle = "#0b0b0b";
    ctx.lineWidth = 2;
    ctx.strokeRect(frameX, frameY, frameW, frameH);

    // Caption block
    ctx.fillStyle = "#a67a3f";
    ctx.fillRect(capX, capY, 26, 2);

    ctx.fillStyle = "#0b0b0b";
    const monoSize = Math.round(W * 0.0095);
    ctx.font = `500 ${monoSize}px "JetBrains Mono", monospace`;
    ctx.textAlign = "left";
    ctx.fillText(("№ " + pad(STYLES.indexOf(style) + 1) + " · " + style.token).toUpperCase(), capX + 40, capY + 6);

    const mainTitle = state.lang === "zh" ? style.cnName : style.name;
    const subTitle  = state.lang === "zh" ? style.name : style.cnName;

    const titlePx = Math.round(W * (state.lang === "zh" ? 0.04 : 0.045));
    ctx.font = `400 ${titlePx}px "Cormorant Garamond", "Noto Serif SC", serif`;
    ctx.textAlign = "left";
    ctx.fillText(mainTitle, capX, capY + 60);

    const subPx = Math.round(W * 0.02);
    ctx.font = `300 ${subPx}px "Cormorant Garamond", "Noto Serif SC", serif`;
    ctx.fillStyle = "#a67a3f";
    ctx.fillText(subTitle, capX, capY + 60 + subPx + 10);

    const dividerY = capY + 60 + subPx + 30;
    ctx.strokeStyle = "#0b0b0b"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(capX, dividerY); ctx.lineTo(capX + capW, dividerY); ctx.stroke();

    // Bilingual commentary — Medium + Strokes + Vibe
    ctx.fillStyle = "#0b0b0b";
    const labelPx = Math.round(W * 0.008);
    const bodyPx = Math.round(W * 0.0125);
    const lineH = Math.round(bodyPx * 1.55);
    const colGap = Math.round(capW * 0.04);
    const colW = Math.round((capW - colGap) / 2);

    const colYStart = dividerY + Math.round(H * 0.022);
    ctx.font = `500 ${labelPx}px "JetBrains Mono", monospace`;
    ctx.textAlign = "left";
    ctx.fillText(t("m.medium").toUpperCase(), capX, colYStart);
    ctx.fillText(t("m.strokes").toUpperCase(), capX + colW + colGap, colYStart);

    ctx.font = `400 ${bodyPx}px "Cormorant Garamond", "Noto Serif SC", serif`;
    wrapText(ctx, style.medium, capX, colYStart + Math.round(labelPx * 2), colW, lineH);
    wrapText(ctx, style.strokes, capX + colW + colGap, colYStart + Math.round(labelPx * 2), colW, lineH);

    // Vibe row (single column below)
    const vibeY = colYStart + Math.round(labelPx * 2) + lineH * 4 + Math.round(H * 0.01);
    ctx.font = `500 ${labelPx}px "JetBrains Mono", monospace`;
    ctx.fillText(t("m.vibe").toUpperCase(), capX, vibeY);
    ctx.font = `400 ${bodyPx}px "Cormorant Garamond", "Noto Serif SC", serif`;
    wrapText(ctx, style.vibe, capX, vibeY + Math.round(labelPx * 2), capW, lineH);

    // Archive footer
    ctx.fillStyle = "#0b0b0b";
    const footPx = Math.round(W * 0.0088);
    ctx.font = `500 ${footPx}px "JetBrains Mono", monospace`;
    ctx.textAlign = "left";
    ctx.fillText(style.designer.toUpperCase(), marginInner + 24, H - marginInner - 16);
    ctx.textAlign = "center";
    ctx.fillText((state.aiBitmap ? "GEMINI · " : "CSS LENS · ") + style.token.toUpperCase(), W / 2, H - marginInner - 16);
    ctx.textAlign = "right";
    ctx.fillText("RENDERING-LANGUAGE ARCHIVE · MMXXVI", W - marginInner - 24, H - marginInner - 16);

    dl.hidden = false;
    if (share) share.hidden = false;
  }

  function paintGrain(ctx, W, H) {
    ctx.save();
    ctx.globalAlpha = 0.04;
    ctx.fillStyle = "#0b0b0b";
    for (let i = 0; i < 900; i++) {
      ctx.fillRect(Math.random() * W, Math.random() * H, 1, 1);
    }
    ctx.restore();
  }

  function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
    const words = String(text || "").split(" ");
    let line = "", dy = 0;
    for (const w of words) {
      const test = line ? line + " " + w : w;
      if (ctx.measureText(test).width > maxWidth && line) {
        ctx.fillText(line, x, y + dy); line = w; dy += lineHeight;
      } else { line = test; }
    }
    if (line) ctx.fillText(line, x, y + dy);
  }

  /* ───────── DOWNLOAD ───────── */
  function setupDownload() {
    $("#download-poster")?.addEventListener("click", () => {
      const canvas = $("#poster-canvas");
      const a = document.createElement("a");
      a.download = `draftelier-${state.selectedStyleId}-${Date.now()}.png`;
      a.href = canvas.toDataURL("image/png");
      a.click();
    });
  }

  /* ───────── SHARE ───────── */
  function setupShare() {
    const btn = $("#share-poster");
    if (!btn) return;
    btn.addEventListener("click", async () => {
      const canvas = $("#poster-canvas");
      const style = STYLES.find((s) => s.id === state.selectedStyleId);
      canvas.toBlob(async (blob) => {
        if (!blob) return;
        const file = new File([blob], `draftelier-${state.selectedStyleId}.png`, { type: "image/png" });
        const shareData = {
          title: "Draftelier",
          text: `${style ? (state.lang === "zh" ? style.cnName : style.name) : "Draftelier"} — Rendering Language Archive`,
          files: [file]
        };
        try {
          if (navigator.canShare && navigator.canShare({ files: [file] })) {
            await navigator.share(shareData);
            return;
          }
        } catch (_) { /* fallthrough */ }
        // Fallback: copy image to clipboard
        try {
          await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
          setStatus(state.lang === "zh" ? "已复制图片到剪贴板" : "Image copied to clipboard");
        } catch (err) {
          setStatus((state.lang === "zh" ? "分享失败：" : "Share failed: ") + err.message, true);
        }
      }, "image/png");
    });
  }

  /* ───────── ASPECT TOGGLE ───────── */
  function setupAspect() {
    $$(".aspect-toggle button").forEach((b) => {
      b.addEventListener("click", () => {
        $$(".aspect-toggle button").forEach((x) => x.classList.remove("active"));
        b.classList.add("active");
        state.aspect = b.dataset.aspect;
        renderPoster();
      });
    });
  }

  /* ───────── STATUS ───────── */
  function setStatus(msg, isError) {
    const el = $("#ai-status");
    if (!el) return;
    if (!msg) { el.hidden = true; el.textContent = ""; return; }
    el.hidden = false;
    el.textContent = msg;
    el.classList.toggle("err", !!isError);
  }

  /* ───────── GEMINI VIA MAKE.COM ───────── */
  function buildStylePrompt(style) {
    const garment = state.lang === "zh"
      ? "保留照片中人物的姿态、轮廓、身体比例与服装结构。不要改变版型或身份。"
      : "Preserve the subject's pose, silhouette, body proportions and garment structure. Do not change the pattern or identity.";
    return [
      `Redraw this photograph in the visual language of "${style.name}" (${style.cnName}).`,
      `Lineage: ${style.lineageEn}`,
      `Medium: ${style.medium}.`,
      `Strokes: ${style.strokes}.`,
      `Vibe: ${style.vibe}.`,
      `Training token: ${style.token}.`,
      garment,
      "Output: a single editorial fashion illustration. No logos, no text, no watermark.",
      `Aspect: ${resolveAspect().w > resolveAspect().h ? "landscape" : "portrait"}.`
    ].join(" ");
  }

  function dataUrlToBase64(dataUrl) {
    const comma = dataUrl.indexOf(",");
    return dataUrl.substring(comma + 1);
  }
  function dataUrlMime(dataUrl) {
    const m = /^data:([^;]+);/.exec(dataUrl);
    return m ? m[1] : "image/jpeg";
  }

  async function callMakeWebhook() {
    if (!MAKE_WEBHOOK_URL) {
      setStatus(state.lang === "zh"
        ? "未配置 Make webhook。打开 assets/app.js，把 MAKE_WEBHOOK_URL 填为 Make 生成的地址。"
        : "Make webhook not configured. Edit assets/app.js and set MAKE_WEBHOOK_URL.", true);
      return;
    }
    if (!state.imageDataUrl) return;
    const style = STYLES.find((s) => s.id === state.selectedStyleId);
    if (!style) return;

    const btn = $("#generate-ai");
    btn.disabled = true;
    setStatus(state.lang === "zh" ? "正在通过 Make → Gemini 渲染…" : "Rendering via Make → Gemini…");

    try {
      const payload = {
        image_base64: dataUrlToBase64(state.imageDataUrl),
        mime_type: dataUrlMime(state.imageDataUrl),
        style_prompt: buildStylePrompt(style),
        style_id: style.id,
        style_token: style.token,
        model: GEMINI_MODEL_PRIMARY,
        fallback_model: GEMINI_MODEL_FALLBACK,
        aspect: resolveAspect().w > resolveAspect().h ? "landscape" : "portrait"
      };
      const res = await fetch(MAKE_WEBHOOK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      if (!data || !data.image_base64) throw new Error("No image_base64 in response");
      const img = new Image();
      img.onload = () => {
        state.aiBitmap = img;
        setStatus((state.lang === "zh" ? "已生成 · 使用模型 " : "Rendered · model ") + (data.model || "?"));
        renderPoster();
      };
      img.onerror = () => setStatus(state.lang === "zh" ? "图片解码失败" : "Failed to decode image", true);
      img.src = "data:image/png;base64," + data.image_base64;
    } catch (err) {
      setStatus((state.lang === "zh" ? "生成失败：" : "Generation failed: ") + err.message, true);
    } finally {
      btn.disabled = false;
    }
  }

  function setupGenerate() {
    const btn = $("#generate-ai");
    if (!btn) return;
    btn.addEventListener("click", callMakeWebhook);
  }

  /* ───────── ARCHIVE ───────── */
  function renderCards(filter = "all") {
    state.currentFilter = filter;
    const list = STYLES.filter((s) =>
      filter === "ready" ? s.loraReady : filter === "preview" ? !s.loraReady : true
    );
    const grid = $("#archive-grid");
    grid.innerHTML = list.map((s) => {
      const idx = STYLES.indexOf(s);
      const title = state.lang === "zh" ? s.cnName : s.name;
      const sub   = state.lang === "zh" ? s.name : s.cnName;
      const desc  = state.lang === "zh" ? (s.researchNotesCn || s.enDesc) : (s.enDesc);
      return `
        <article class="card" data-id="${s.id}">
          <div class="num">№ ${pad(idx + 1)} · ${s.token}</div>
          <h3 class="title">${title}</h3>
          <div class="cn">${sub}</div>
          <div class="designer">${s.designer}</div>
          <p class="desc">${desc}</p>
          <div class="foot">
            <span class="badge ${s.loraReady ? "ready" : ""}">${s.loraReady ? t("m.ready") : t("m.preview")}</span>
            <span>${t("c.open")}</span>
          </div>
        </article>`;
    }).join("");
    $$(".card", grid).forEach((card) =>
      card.addEventListener("click", () => openModal(card.dataset.id))
    );
  }

  /* ───────── MODAL ───────── */
  function openModal(id) {
    const s = STYLES.find((x) => x.id === id);
    if (!s) return;
    state.openModalId = id;
    const idx = STYLES.findIndex((x) => x.id === id);
    const title = state.lang === "zh" ? s.cnName : s.name;
    const sub   = state.lang === "zh" ? s.name : s.cnName;
    const lineage = state.lang === "zh" ? s.lineageCn : s.lineageEn;
    const notes = state.lang === "zh" ? s.researchNotesCn : s.editorialDesc;

    $("#modal-body").innerHTML = `
      <div class="num">№ ${pad(idx + 1)} · ${s.token}</div>
      <h3>${title}</h3>
      <div class="sub-cn">${sub}</div>
      <div style="margin-bottom:6px">
        <span class="chip ${s.loraReady ? "ready" : ""}">${s.loraReady ? t("m.ready") : t("m.preview")}</span>
        <span class="chip">${s.designer}</span>
      </div>
      <dl>
        <dt>${t("m.lineage")}</dt>
        <dd>${lineage}</dd>
        <dt>${t("m.medium")}</dt><dd>${s.medium}</dd>
        <dt>${t("m.strokes")}</dt><dd>${s.strokes}</dd>
        <dt>${t("m.vibe")}</dt><dd>${s.vibe}</dd>
        <dt>${t("m.notes")}</dt><dd>${notes}</dd>
        <dt>${t("m.token")}</dt>
        <dd><code class="token">${s.token}</code></dd>
      </dl>
      <a class="cta-open-studio" href="#atelier">${t("m.open")}</a>
    `;
    $("#modal").classList.add("open");
    document.body.style.overflow = "hidden";
    $(".cta-open-studio", $("#modal-body"))?.addEventListener("click", () => {
      selectStyle(s.id);
      closeModal();
    });
  }
  function closeModal() {
    $("#modal").classList.remove("open");
    document.body.style.overflow = "";
    state.openModalId = null;
  }

  /* ───────── WIRING ───────── */
  function setupFilters() {
    $$(".filter-bar button").forEach((btn) =>
      btn.addEventListener("click", () => {
        $$(".filter-bar button").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        renderCards(btn.dataset.filter);
      })
    );
  }
  function setupModal() {
    $("#modal .close").addEventListener("click", closeModal);
    $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") closeModal(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });
  }
  function setupLang() {
    $$(".lang-toggle button").forEach((b) =>
      b.addEventListener("click", () => setLang(b.dataset.lang))
    );
  }

  document.addEventListener("DOMContentLoaded", () => {
    setupLang();
    setupDropzone();
    setupDownload();
    setupShare();
    setupAspect();
    setupGenerate();
    setupModal();
    initMarquee();
    applyI18n(); // initial render
  });
})();
