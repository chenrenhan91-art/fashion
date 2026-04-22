/*
 * Draftelier — Designer Rendering-Language Archive
 * Pure data. No framework. Loaded as a classic <script> so it also works under file://.
 *
 * Each entry describes ONE rendering language (not a garment design).
 * The "renderNotes" are what the sketch engine uses when redrawing an uploaded photo.
 */
(function (global) {
  const GITHUB_REPO = "zry19950621-star/fashionmarker-ai";
  const GITHUB_REF = "main";
  const LORA_ROOT = "training-runs";

  const STYLES = [
    {
      id: "dior",
      designer: "Christian Dior",
      name: "Parisian Couture",
      cnName: "巴黎高定轮廓",
      token: "paris_new_look",
      lineageEn: "Echoes the visual language of Christian Dior.",
      lineageCn: "灵感谱系向 Christian Dior 的高定语言致意。",
      enDesc: "Soft graphite lines, poised structure, and polished couture restraint.",
      editorialDesc: "Delicate pencil construction and sheer watercolor softness with refined couture balance.",
      medium: "highly expressive, delicate graphite pencil construction lines with a translucent, soft watercolor wash",
      strokes: "sweeping elegant curves, poised line control, polished vintage archival sketching",
      vibe: "1950s salon poise, refined couture restraint, elegant and effortless",
      researchNotesCn: "致敬 1950 年代 Dior 御用插画大师 Rene Gruau。强调沙龙里的从容优雅、New Look 式沙漏轮廓，以及水彩半透明的轻柔纸面感。",
      loraReady: true,
      loraRun: "paris-new-look-dior-pinterest-batch2"
    },
    {
      id: "balenciaga",
      designer: "Cristobal Balenciaga",
      name: "Sculptural Elegance",
      cnName: "建构优雅",
      token: "architectural_volume",
      lineageEn: "Inspired by the sculptural discipline of Cristobal Balenciaga.",
      lineageCn: "灵感谱系借鉴 Cristobal Balenciaga 的雕塑式剪裁语汇。",
      enDesc: "Measured contours, sculpted volume, and quiet atelier precision.",
      editorialDesc: "Restrained graphite contours and cool gouache shading create a sculpted editorial page.",
      medium: "cool, precise graphite contour lines with restrained, flat gouache wash",
      strokes: "measured contours, structural tailoring cues, bold negative space control",
      vibe: "cerebral, sculptural, disciplined, quiet atelier precision",
      researchNotesCn: "Balenciaga 被称为“时装界的建筑师”。重点不是装饰，而是内部结构、空间控制、茧型和布袋裙等雕塑化体量关系。",
      loraReady: true,
      loraRun: "architectural-volume-balenciaga-batch2"
    },
    {
      id: "schiaparelli",
      designer: "Schiaparelli",
      name: "Surreal Ornament",
      cnName: "超现实华饰",
      token: "surreal_gold",
      lineageEn: "Echoes the surreal wit associated with Elsa Schiaparelli.",
      lineageCn: "灵感谱系呼应 Elsa Schiaparelli 式超现实装饰张力。",
      enDesc: "Ink contrast and luminous accents with poetic surreal tension.",
      editorialDesc: "Sharp black linework and luminous metallic accents create a vivid surreal editorial mood.",
      medium: "sharp, aggressive black India ink outlines clashing with luminous metallic gold leaf accents",
      strokes: "eccentric drafting gestures, trompe l'oeil detailing, sharp decorative contrast",
      vibe: "avant-garde couture energy, poetic surreal tension, bold and dramatic",
      researchNotesCn: "Elsa Schiaparelli 与达利合作的超现实语汇非常关键。强调黑色墨线与金属金箔、错视画装饰、戏剧化配件和怪诞张力。",
      loraReady: true,
      loraRun: "surreal-gold-schiaparelli-batch3-fast"
    },
    {
      id: "chanel",
      designer: "Karl Lagerfeld",
      name: "Modern Croquis",
      cnName: "现代速写气场",
      token: "modern_croquis",
      lineageEn: "Carries the brisk editorial cadence often linked to Karl Lagerfeld.",
      lineageCn: "灵感谱系带有 Karl Lagerfeld 式利落速写与编辑感节奏。",
      enDesc: "Rapid strokes, backstage energy, and unfinished confidence.",
      editorialDesc: "Aggressive marker movement and crisp highlights preserve the pulse of a live editorial fitting.",
      medium: "rapid, thick black marker strokes, pastel smudges, and dynamic white correction-fluid highlights",
      strokes: "fast croquis sweeps, abrupt marker accents, live-fitting spontaneity",
      vibe: "backstage editorial energy, messy confidence, spontaneous and chic",
      researchNotesCn: "强调老佛爷后台速写的即时性：粗黑马克笔、眼影盘般的粉彩晕染、白色修正液高光，以及未完成却极有节奏的编辑感。",
      loraReady: true,
      loraRun: "modern-croquis-karl-pinterest-batch4"
    },
    {
      id: "mugler",
      designer: "Thierry Mugler",
      name: "Futurist Glamour",
      cnName: "未来戏剧感",
      token: "insect_power",
      lineageEn: "Inspired by the theatrical futurism of Thierry Mugler.",
      lineageCn: "灵感谱系向 Thierry Mugler 的未来戏剧性轮廓致意。",
      enDesc: "Sharp contrast, engineered detail, and bold editorial intensity.",
      editorialDesc: "Knife-sharp linework and glossy accents push the image toward a futuristic couture spectacle.",
      medium: "knife-sharp fineliner contour lines, high-contrast flat marker shading, glossy reflective highlights",
      strokes: "engineered linework, hyper-exaggerated hourglass structure, cyborg and insectoid motifs",
      vibe: "runway-scale drama, futuristic seduction, hard-edged theatrical glamour",
      researchNotesCn: "Mugler 草图带有昆虫、机械体和超夸张沙漏形的未来身体观。重点是黑白反差、反光乳胶与金属质感、舞台级张力。",
      loraReady: true,
      loraRun: "insect-power-second-batch-mugler-v2"
    },
    {
      id: "galliano",
      designer: "John Galliano",
      name: "Baroque Narrative",
      cnName: "华丽叙事",
      token: "baroque_narrative",
      lineageEn: "Echoes the romantic pageantry associated with John Galliano.",
      lineageCn: "灵感谱系呼应 John Galliano 式浪漫而华丽的叙事能量。",
      enDesc: "Opulent layering, romantic movement, and couture theatrics in motion.",
      editorialDesc: "Rich wash, embellished notation, and romantic linework turn the page into a lavish fashion story.",
      medium: "expressive, swirling ink linework with lavish, opulent watercolor layering",
      strokes: "historical dressmaking annotations, passionate movement, raw embellished notation",
      vibe: "chaotic beauty, dramatic narrative, romantic theatricality, raw and passionate",
      researchNotesCn: "Galliano 的手稿像一部疯狂的历史小说：旋涡般墨线、水彩泼溅、服装史和面料批注并行，带着失控而华美的戏剧叙事。",
      loraReady: true,
      loraRun: "baroque-narrative-galliano-pinterest-batch4"
    },
    {
      id: "gaultier",
      designer: "Jean Paul Gaultier",
      name: "Corset Cabaret",
      cnName: "紧身华宴",
      token: "corset_cabaret",
      lineageEn: "Carries hints of Jean Paul Gaultier's body-conscious irreverence.",
      lineageCn: "灵感谱系带有 Jean Paul Gaultier 式身体意识与戏谑精神。",
      enDesc: "Sinuous lines, corseted structure, and decadent performance flair.",
      editorialDesc: "Tattoo-like contour and corseted notation create a theatrical, body-conscious editorial page.",
      medium: "precise tattoo-like black contour lines with intricate ballpoint pen corsetry seam notation",
      strokes: "body-conscious contour tracing, cabaret styling cues, fetish-tailoring seam detail",
      vibe: "subversive, playful, sensual, decadent editorial tension",
      researchNotesCn: "Jean Paul Gaultier 的画面常把水手、束身胸衣、内衣外穿与纹身式线条混在一起，重点在身体意识和表演性时尚。",
      loraReady: true,
      loraRun: "corset-cabaret-gaultier-batch4"
    },
    {
      id: "westwood",
      designer: "Vivienne Westwood",
      name: "Punk Aristocracy",
      cnName: "朋克宫廷",
      token: "punk_rococo",
      lineageEn: "Inspired by the rebellious historicism of Vivienne Westwood.",
      lineageCn: "灵感谱系借鉴 Vivienne Westwood 式叛逆历史感与宫廷错位。",
      enDesc: "Disrupted tailoring, rebellious linework, and historical attitude re-cut.",
      editorialDesc: "Anarchic pen gestures and subverted drape logic create a rebellious salon mood.",
      medium: "anarchic biro ballpoint pen and sketchy ink lines with collage-like color blocking",
      strokes: "disrupted historic drape, subverted tailoring, tartan and tweed notation, raw scratched marks",
      vibe: "rebellious, DIY, aristocratic mischief, punk editorial attitude",
      researchNotesCn: "Vivienne Westwood 的手稿语言来自 DIY 拼贴、无政府主义、英伦古典与破坏性剪裁的碰撞，尤其是格纹、粗糙笔线与历史服装错位。",
      loraReady: true,
      loraRun: "punk-rococo-westwood-batch4"
    },
    {
      id: "maison_margiela",
      designer: "Maison Margiela",
      name: "Deconstructed Modern",
      cnName: "解构现代",
      token: "artisanal_deconstruction",
      lineageEn: "Echoes the quiet deconstruction associated with Martin Margiela.",
      lineageCn: "灵感谱系呼应 Martin Margiela 式克制而静默的解构语言。",
      enDesc: "Faint traces, erased edges, and artisanal restraint.",
      editorialDesc: "Light graphite residue and washed archive texture keep the page quiet, cerebral, and spare.",
      medium: "extremely faint, ghostly graphite outlines with deliberately erased construction marks and grayscale xerox-like texture",
      strokes: "sparse pattern-study notation, basting stitches, nearly vanishing contour residue",
      vibe: "quiet radical restraint, anonymous beauty, cerebral artisanal deconstruction",
      researchNotesCn: "Margiela 的纸面感常是匿名、发白、未完成的：幽灵般铅笔印、被擦掉的结构线、打样记号、假缝线和复印机般的灰度失真。",
      loraReady: false,
      loraRun: "artisanal-deconstruction-margiela-batch1"
    },
    {
      id: "iris_van_herpen",
      designer: "Iris van Herpen",
      name: "Bionic Motion",
      cnName: "仿生流线",
      token: "bionic_couture",
      lineageEn: "Inspired by the kinetic geometry of Iris van Herpen.",
      lineageCn: "灵感谱系向 Iris van Herpen 的动态几何与仿生结构致意。",
      enDesc: "Technical geometry with kinetic, near-organic movement.",
      editorialDesc: "Meticulous fineliner structure and wireframe rhythm create a futuristic, almost living silhouette.",
      medium: "meticulous, ultra-fine technical drafting pen lines with complex living wireframe grids",
      strokes: "parametric geometry, translucent synthetic layering, kinetic organic contour systems",
      vibe: "avant-garde techno-couture, futuristic, precise, almost bio-digital",
      researchNotesCn: "Iris van Herpen 的手稿更接近 CAD 与参数化结构研究，像神经网格、显微镜下的有机体或 3D 打印前的技术草案。",
      loraReady: true,
      loraRun: "bionic-couture-iris-batch3"
    },
    {
      id: "issey_miyake",
      designer: "Issey Miyake",
      name: "Pleated Velocity",
      cnName: "褶裥动势",
      token: "pleated_motion",
      lineageEn: "Carries echoes of Issey Miyake's pleated movement studies.",
      lineageCn: "灵感谱系带有 Issey Miyake 式褶裥研究与轻盈动势。",
      enDesc: "Pleat logic, airy motion, and sculpted lightness.",
      editorialDesc: "Fold studies and luminous movement cues keep the drawing fluid, technical, and weightless.",
      medium: "airy and sweeping graphite lines with precise micro-pleat notation and fluid watercolor washes",
      strokes: "origami fold logic, kinetic drape motion, sculptural fabric geometry",
      vibe: "minimal, weightless, dynamic, technically lyrical",
      researchNotesCn: "Issey Miyake 的重点是“一块布”和微小褶皱的几何逻辑，不必依赖人物本身，而是把布料在空气中的动势与折纸结构画出来。",
      loraReady: true,
      loraRun: "pleated-motion-issey-batch4"
    },
    {
      id: "courreges",
      designer: "Andre Courreges",
      name: "Space Age Precision",
      cnName: "太空几何",
      token: "space_age_clean",
      lineageEn: "Inspired by the optimistic futurism of Andre Courreges.",
      lineageCn: "灵感谱系借鉴 Andre Courreges 式乐观太空未来主义。",
      enDesc: "Crisp lines, optical white space, and mod futurism.",
      editorialDesc: "Geometric strokes and disciplined white-space control create a polished future-facing page.",
      medium: "crisp, ruler-straight geometric ink lines with minimal flat vector-like marker wash",
      strokes: "immaculate A-line geometry, strict line discipline, optical white-space control",
      vibe: "mod futurist, polished, optimistic retro-future, immaculate precision",
      researchNotesCn: "Andre Courreges 的精神来自 1960 年代太空竞赛与 mod 几何：绝对直的尺规线、A 字轮廓、矢量般留白和乐观冷静的未来感。",
      loraReady: true,
      loraRun: "space-age-courreges-pinterest-batch4"
    },
    {
      id: "rabanne",
      designer: "Paco Rabanne",
      name: "Metallic Modularism",
      cnName: "金属模块",
      token: "metal_modular",
      lineageEn: "Echoes the industrial modularity associated with Paco Rabanne.",
      lineageCn: "灵感谱系呼应 Paco Rabanne 式工业金属与模块化结构。",
      enDesc: "Reflective edges, modular construction, and industrial couture clarity.",
      editorialDesc: "Reflective accents and assembly cues bring hard-edged precision to the editorial silhouette.",
      medium: "sharp reflective ink edges with shimmering metallic marker shading and precise modular hardware assembly notes",
      strokes: "chainmail and disc construction detail, hard-edged assembly cues, metallic surface rhythm",
      vibe: "industrial couture, space-age hardness, cold shine, modular precision",
      researchNotesCn: "Paco Rabanne 的服装像工业组装而非缝纫，关键是锁环、金属片、锁子甲和硬反光边缘，画面应像一张未来工业图纸。",
      loraReady: true,
      loraRun: "metal-modular-rabanne-batch2"
    },
    {
      id: "gucci",
      designer: "Alessandro Michele",
      name: "Romantic Maximalism",
      cnName: "浪漫极繁",
      token: "maximalist_romance",
      lineageEn: "Carries traces of Alessandro Michele's layered romanticism.",
      lineageCn: "灵感谱系带有 Alessandro Michele 式层叠浪漫与复古丰盛感。",
      enDesc: "Layered color, quirky richness, and expressive editorial warmth.",
      editorialDesc: "Messy pencils and saturated wash create an eccentric, story-rich editorial fairytale.",
      medium: "heavily layered colored pencils, saturated watercolors, expressive doodle-like strokes",
      strokes: "ornamental layering, retro print notation, whimsical dense page filling",
      vibe: "eccentric, gender-fluid, story-rich, vibrant maximalist romanticism",
      researchNotesCn: "Michele 时期 Gucci 像复古童话：高饱和彩铅、古怪花纹、性别流动气质、文艺复兴式繁复层叠与故事书般的页面密度。",
      loraReady: true,
      loraRun: "maximalist-romance-gucci-pinterest-batch4"
    },
    {
      id: "mcqueen",
      designer: "Alexander McQueen",
      name: "Dark Poise",
      cnName: "暗调锋度",
      token: "gothic_theatre",
      lineageEn: "Inspired by the sharp theatricality of Lee Alexander McQueen.",
      lineageCn: "灵感谱系向 Lee Alexander McQueen 的锋利戏剧性致意。",
      enDesc: "Smudged depth, sharp scratches, and poised gothic emotion.",
      editorialDesc: "Charcoal density and razor graphite marks create a dark but composed couture mood.",
      medium: "heavily smudged emotional charcoal with razor-sharp aggressive graphite scratchings",
      strokes: "dark tonal buildup, blade-like marks, gothic tailoring emphasis, macabre line tension",
      vibe: "dark romanticism, composed violence, dramatic couture poise, beautifully macabre",
      researchNotesCn: "McQueen 的关键是裁缝精度与病态浪漫并存：木炭的厚重污痕、刀刻般石墨线、黑暗情绪意象和极其锋利的结构控制。",
      loraReady: true,
      loraRun: "gothic-theatre-mcqueen-pinterest-batch4"
    },
    {
      id: "ysl",
      designer: "Yves Saint Laurent",
      name: "Minimal Precision",
      cnName: "极简精裁",
      token: "minimalist_chic",
      lineageEn: "Echoes the refined restraint associated with Yves Saint Laurent.",
      lineageCn: "灵感谱系呼应 Yves Saint Laurent 式极简而锋利的精裁语汇。",
      enDesc: "Sparse lines, bold blocking, and elegant negative space.",
      editorialDesc: "Disciplined ink outlines and sharp blocking keep the page spare, sleek, and exact.",
      medium: "extraordinarily sparse, precise black ink outlines with flat, bold, minimalist marker color blocking",
      strokes: "razor-sleek tailoring lines, sharp shoulders, elegant negative space discipline",
      vibe: "sophisticated Parisian chic, restrained, exact, modernist elegance",
      researchNotesCn: "Yves Saint Laurent 的时装手稿以极少线条完成高强度剪裁判断，Le Smoking 式修长结构、纯色平涂和克制的巴黎精裁气质是核心。",
      loraReady: true,
      loraRun: "minimalist-chic-ysl-batch3"
    }
  ];

  // derive LoRA paths / GitHub URLs (same convention as the original project)
  const enriched = STYLES.map((s) => {
    const loraWeightPath = s.loraRun
      ? `${LORA_ROOT}/${s.loraRun}/pytorch_lora_weights.safetensors`
      : null;
    return {
      ...s,
      tag: `${s.name.toUpperCase()} · ${s.cnName}`,
      githubRepo: GITHUB_REPO,
      githubRef: GITHUB_REF,
      loraWeightPath,
      loraWeightUrl: loraWeightPath
        ? `https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_REF}/${loraWeightPath}`
        : null,
      loraWeightGithubUrl: loraWeightPath
        ? `https://github.com/${GITHUB_REPO}/blob/${GITHUB_REF}/${loraWeightPath}`
        : null
    };
  });

  global.DRAFTELIER_STYLES = enriched;
  global.DRAFTELIER_META = {
    repo: GITHUB_REPO,
    ref: GITHUB_REF,
    loraRoot: LORA_ROOT,
    total: enriched.length,
    ready: enriched.filter((s) => s.loraReady).length
  };
})(window);
