/**
 * Draftelier · 跑马灯图库配置
 * ─────────────────────────────────────────────────────────
 * 在下方 DRAFTELIER_GALLERY 数组中填入你的图片。
 * 跑马灯会自动复制一遍以实现无缝循环，建议放 6–12 张。
 *
 * 每条格式：
 *   src   — 图片路径（相对于网站根目录），如 "assets/gallery/01.jpg"
 *           支持：JPG / PNG / WebP / SVG
 *   label — 卡片底部说明（不超过 36 个字符）
 *   frame — 边框风格（三选一）：
 *             "archive"   双线边框 + 对角金色菱形
 *             "bracket"   四角 L 形墨色括号
 *             "editorial" 单线 + 金色分割线 + 编号标签
 *
 * 替换步骤：
 *   1. 把你的图片放入 assets/gallery/ 文件夹
 *   2. 修改下方 src 路径
 *   3. 保存后刷新浏览器即可看到效果
 * ─────────────────────────────────────────────────────────
 */
(function (global) {
  global.DRAFTELIER_GALLERY = [
    {
      src:   "assets/gallery/p1.svg",
      label: "Silhouette Study · Vol. I",
      frame: "archive"
    },
    {
      src:   "assets/gallery/p2.svg",
      label: "Drape Construction",
      frame: "bracket"
    },
    {
      src:   "assets/gallery/p3.svg",
      label: "Neckline Archive",
      frame: "editorial"
    },
    {
      src:   "assets/gallery/p4.svg",
      label: "Surface & Texture",
      frame: "archive"
    },
    {
      src:   "assets/gallery/p5.svg",
      label: "Proportion Grid",
      frame: "bracket"
    },
    {
      src:   "assets/gallery/p6.svg",
      label: "Ornamental Study",
      frame: "editorial"
    },
    {
      src:   "assets/gallery/p7.svg",
      label: "Atelier Reference",
      frame: "archive"
    },
    {
      src:   "assets/gallery/p8.svg",
      label: "Mesh & Structure",
      frame: "bracket"
    }
  ];
})(window);
