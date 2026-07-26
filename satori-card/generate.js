#!/usr/bin/env node
/**
 * Satori Card Generator  (tool-call layer)
 * HTML/CSS -> SVG -> PNG shareable cards with QR code
 *
 * Architecture:  skill  ->  tool call  ->  page generation
 *   - This file is the "tool call" layer (invoked by SKILL.md, or as a
 *     subprocess renderer by card_generator/generate_card.py --renderer satori)
 *   - Themes are loaded from the shared ../themes.json (single source of
 *     truth, shared with the Python renderer)
 *   - Output images are the "page generation" layer
 *
 * Usage (landscape card):
 *   node generate.js --url https://example.com --name "Kimi K3" --image logo.png
 *
 * Usage (social portrait card with feature bullets):
 *   node generate.js --url https://example.com --name "Kimi K3" --image logo.png \
 *     --type social --subtitle "新一�?AI 模型" --f1 "AI 对话" --f2 "多模�?
 *
 * Usage (square format):
 *   node generate.js --url https://example.com --name "Kimi K3" --image logo.png --type square
 */

import { readFileSync, writeFileSync } from "fs";
import { resolve, basename, dirname } from "path";
import { fileURLToPath } from "url";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import QRCode from "qrcode";

// ============================================================
//  SHARED THEME LOADER  (single source of truth: themes.json)
// ============================================================

const __dirname = dirname(fileURLToPath(import.meta.url));
const THEMES_FILE = resolve(__dirname, "..", "themes.json");
const SHARED = JSON.parse(readFileSync(THEMES_FILE, "utf-8"));

/** Normalize a theme entry from themes.json into the shape this renderer uses. */
function normalizeTheme(t) {
  const c = t.colors;
  const sh = t.shadow;
  return {
    name: t.name,
    bg: c.canvas_bg,
    cardBg: c.card_bg,
    heroBg: c.card_bg, // derived; gradient base
    text: c.text_primary,
    textSec: c.text_secondary,
    accent: c.accent,
    accentDim: c.accent_alt,
    divider: c.divider,
    shadowRgba: `rgba(${sh.r},${sh.g},${sh.b},${(sh.a / 255).toFixed(3)})`,
    dark: t.dark,
  };
}

const THEMES = Object.fromEntries(
  Object.entries(SHARED.themes).map(([k, v]) => [k, normalizeTheme(v)])
);
const FORMATS = SHARED.formats;

// ============================================================
//  CLI
// ============================================================

const args = process.argv.slice(2);
const getArg = (name) => {
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : null;
};

const url = getArg("--url");
const name = getArg("--name");
let imagePath = getArg("--image");
const themeName = getArg("--theme") || "tech-innovation";
const type = getArg("--type") || "landscape";
const subtitle = getArg("--subtitle") || "";
const feature1 = getArg("--f1") || "";
const feature2 = getArg("--f2") || "";
const feature3 = getArg("--f3") || "";
const accentOverride = getArg("--accent") || "";
const brand = getArg("--brand") || "";
const platform = getArg("--platform") || "";
const lang = getArg("--lang") || "en";
const outputPath = getArg("--output") || "card.png";

// Unified per-card copy (international default = en).
const LOCALES = {
  en: { badge: "NEW RELEASE", scanHint: "SCAN TO VISIT", defaultSubtitle: "Now Available" },
  zh: { badge: "全新发布", scanHint: "扫码访问", defaultSubtitle: "现已上线" },
};
const L = LOCALES[lang] || LOCALES.en;

if (!url || !name || !imagePath) {
  console.error("Usage: node generate.js --url <URL> --name <Name> --image <path> [--type social|landscape|square] [--theme tech] [--subtitle text] [--f1 feature] [--f2 feature] [--f3 feature] [--accent #hex] [--brand text] [--platform text] [--lang en|zh] [--output card.png]");
  process.exit(1);
}

imagePath = resolve(imagePath);

const theme = { ...THEMES[themeName] || THEMES["tech-innovation"] };
if (accentOverride) theme.accent = accentOverride;

const isDark = theme.dark;
const isSocial = type === "social";
const isSquare = type === "square";

const fmt = FORMATS[type] || FORMATS.landscape;
const canvasW = fmt.w;
const canvasH = fmt.h;
const cardMargin = isSocial ? 20 : 24;

// ============================================================
//  FONT LOADING
// ============================================================

const fontDir = (process.env.WINDIR || "C:\\Windows") + "/Fonts/";
function loadFont(file) {
  try { return readFileSync(fontDir + file); } catch {
    try { return readFileSync(file); } catch { return null; }
  }
}

const fonts = [];
const segoeUI = loadFont("segoeui.ttf");
const segoeUIBold = loadFont("segoeuib.ttf");
const segoeUILight = loadFont("segoeuil.ttf");
const simhei = loadFont("simhei.ttf");
const deng = loadFont("Deng.ttf");

if (segoeUI) fonts.push({ name: "Segoe UI", data: segoeUI, weight: 400, style: "normal" });
if (segoeUIBold) fonts.push({ name: "Segoe UI", data: segoeUIBold, weight: 700, style: "normal" });
if (segoeUILight) fonts.push({ name: "Segoe UI", data: segoeUILight, weight: 300, style: "normal" });
if (simhei) fonts.push({ name: "SimHei", data: simhei, weight: 400, style: "normal" });
if (deng && !simhei) fonts.push({ name: "DengXian", data: deng, weight: 400, style: "normal" });

const FF = `"Segoe UI", "SimHei", "DengXian", Arial, sans-serif`;

// ============================================================
//  HELPERS
// ============================================================

function loadImageDataURI(filePath) {
  try {
    const buf = readFileSync(filePath);
    const ext = basename(filePath).split(".").pop().toLowerCase();
    const mime = ext === "png" ? "image/png" : "image/jpeg";
    return `data:${mime};base64,${buf.toString("base64")}`;
  } catch { console.error(`Cannot read: ${filePath}`); process.exit(1); }
}

async function generateQR(url) {
  return await QRCode.toDataURL(url, { width: 400, margin: 2, color: { dark: "#000000", light: "#ffffff" } });
}

const logoURI = loadImageDataURI(imagePath);

// ============================================================
//  SOCIAL PORTRAIT LAYOUT
// ============================================================

function socialCard({ name, subtitle, displayUrl, qrDataURI, feature1, feature2, feature3 }) {
  const t = theme;
  const features = [feature1, feature2, feature3].filter(Boolean);
  if (features.length === 0) features.push("Model Marketplace", "API & SDK Access", "Production Ready");

  const cardW = canvasW - cardMargin * 2;
  const innerPad = 56;
  const isX = themeName === "x-dark";
  // X style shows the wordmark logo across the top; otherwise a centered logo tile.
  const logoTop = isX;

  return {
    type: "div",
    props: {
      style: {
        display: "flex", width: "100%", height: "100%",
        background: t.bg, padding: `${cardMargin}px`, boxSizing: "border-box",
        alignItems: "center", justifyContent: "center",
      },
      children: [
        {
          type: "div",
          props: {
            style: {
              display: "flex", flexDirection: "column",
              width: `${cardW}px`, height: `${canvasH - cardMargin * 2}px`,
              background: t.cardBg, borderRadius: "28px", overflow: "hidden",
              boxShadow: `0 16px 64px ${isDark ? "rgba(0,0,0,0.55)" : "rgba(0,0,0,0.08)"}`,
              border: isX ? `1px solid ${t.divider}` : "none",
              padding: `${innerPad}px`, boxSizing: "border-box",
            },
            children: [
              // --- Top brand row: horizontal wordmark logo ---
              {
                type: "div",
                props: {
                  style: {
                    display: "flex", flexDirection: "row", alignItems: "center",
                    width: "100%",
                  },
                  children: [
                    { type: "img", props: { src: logoURI, style: { height: "42px", objectFit: "contain" } } },
                    { type: "div", props: { style: { flex: 1 } } },
                    ...(platform ? [{ type: "div", props: { style: { fontSize: "13px", fontWeight: 600, color: t.textSec, fontFamily: FF, textTransform: "uppercase", letterSpacing: "2px" }, children: platform } }] : []),
                  ],
                },
              },
              // thin divider under brand row
              { type: "div", props: { style: { width: "100%", height: "1px", background: t.divider, marginTop: "20px" } } },

              // top spacer — balances vertical whitespace
              { type: "div", props: { style: { display: "flex", flex: 1 } } },

              // --- Hero: name + subtitle + feature bullets (vertically centered) ---
              { type: "div", props: { style: { fontSize: "84px", fontWeight: 800, color: t.text, fontFamily: FF, lineHeight: 1.0, letterSpacing: "-3px" }, children: name } },
              { type: "div", props: { style: { fontSize: "23px", fontWeight: 400, color: t.textSec, fontFamily: FF, marginTop: "18px", lineHeight: 1.45 }, children: subtitle || L.defaultSubtitle } },
              // feature bullets (compact)
              {
                type: "div",
                props: {
                  style: { display: "flex", flexDirection: "column", width: "100%", marginTop: "34px" },
                  children: features.map((f, i) => ({
                    type: "div",
                    props: {
                      style: { display: "flex", flexDirection: "row", alignItems: "center", marginBottom: i < features.length - 1 ? "18px" : "0" },
                      children: [
                        { type: "div", props: { style: { display: "flex", alignItems: "center", justifyContent: "center", width: "28px", height: "28px", borderRadius: "14px", background: `${t.accent}1a`, marginRight: "16px", flexShrink: 0 }, children: [{ type: "div", props: { style: { width: "8px", height: "8px", borderRadius: "4px", background: t.accent } } }] } },
                        { type: "div", props: { style: { fontSize: "19px", fontWeight: 500, color: t.text, fontFamily: FF, letterSpacing: "0.2px" }, children: f } },
                      ],
                    },
                  })),
                },
              },

              // bottom spacer — balances vertical whitespace
              { type: "div", props: { style: { display: "flex", flex: 1 } } },

              // --- Footer: QR + CTA/URL ---
              { type: "div", props: { style: { width: "100%", height: "1px", background: t.divider, marginBottom: "26px" } } },
              {
                type: "div",
                props: {
                  style: { display: "flex", flexDirection: "row", alignItems: "center", width: "100%" },
                  children: [
                    {
                      type: "div",
                      props: {
                        style: { display: "flex", alignItems: "center", justifyContent: "center", width: "124px", height: "124px", background: "#ffffff", borderRadius: "16px", overflow: "hidden", padding: "8px", boxSizing: "border-box", flexShrink: 0, marginRight: "24px" },
                        children: [{ type: "img", props: { src: qrDataURI, style: { width: "100%", height: "100%" } } }],
                      },
                    },
                    {
                      type: "div",
                      props: {
                        style: { display: "flex", flexDirection: "column", flex: 1 },
                        children: [
                          { type: "div", props: { style: { fontSize: "12px", fontWeight: 700, color: t.textSec, fontFamily: FF, textTransform: "uppercase", letterSpacing: "2px", marginBottom: "10px" }, children: L.scanHint } },
                          { type: "div", props: { style: { fontSize: "17px", fontWeight: 600, color: t.accent, fontFamily: FF }, children: displayUrl } },
                        ],
                      },
                    },
                  ],
                },
              },
            ],
          },
        },
      ],
    },
  };
}

// ============================================================
//  SQUARE LAYOUT (1:1, centered)
// ============================================================

function squareCard({ name, subtitle, displayUrl, qrDataURI }) {
  const t = theme;
  const cardW = canvasW - cardMargin * 2;
  const cardH = canvasH - cardMargin * 2;

  return {
    type: "div",
    props: {
      style: { display: "flex", width: "100%", height: "100%", background: t.bg, padding: `${cardMargin}px`, boxSizing: "border-box", alignItems: "center", justifyContent: "center" },
      children: [
        {
          type: "div",
          props: {
            style: { display: "flex", flexDirection: "column", alignItems: "center", width: `${cardW}px`, height: `${cardH}px`, background: t.cardBg, borderRadius: "28px", overflow: "hidden", boxShadow: `0 12px 60px ${isDark ? "rgba(0,0,0,0.6)" : "rgba(0,0,0,0.10)"}`, padding: "60px 50px", boxSizing: "border-box" },
            children: [
              // top accent bar
              { type: "div", props: { style: { width: "60px", height: "4px", background: t.accent, borderRadius: "2px", marginBottom: "36px" } } },
              // logo
              {
                type: "div",
                props: {
                  style: { display: "flex", alignItems: "center", justifyContent: "center", width: "160px", height: "160px", background: isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)", borderRadius: "36px", padding: "24px", boxSizing: "border-box", border: `1px solid ${t.divider}`, marginBottom: "32px" },
                  children: [{ type: "img", props: { src: logoURI, style: { maxWidth: "100%", maxHeight: "100%", objectFit: "contain" } } }],
                },
              },
              // name
              { type: "div", props: { style: { fontSize: "56px", fontWeight: 700, color: t.text, fontFamily: FF, lineHeight: 1.1, letterSpacing: "-1px", textAlign: "center" }, children: name } },
              { type: "div", props: { style: { fontSize: "22px", fontWeight: 400, color: t.textSec, fontFamily: FF, marginTop: "14px", textAlign: "center" }, children: subtitle || L.defaultSubtitle } },
              ...(brand || platform ? [{ type: "div", props: { style: { fontSize: "13px", fontWeight: 600, color: t.textSec, fontFamily: FF, textTransform: "uppercase", letterSpacing: "3px", marginTop: "12px", textAlign: "center" }, children: [brand, platform].filter(Boolean).join("  ·  ") } }] : []),
              { type: "div", props: { style: { flex: 1 } } },
              // divider
              { type: "div", props: { style: { width: "100%", height: "1px", background: `linear-gradient(90deg, transparent 0%, ${t.divider} 50%, transparent 100%)`, marginBottom: "28px" } } },
              // QR + url row
              {
                type: "div",
                props: {
                  style: { display: "flex", flexDirection: "row", alignItems: "center", gap: "28px", width: "100%", justifyContent: "center" },
                  children: [
                    {
                      type: "div",
                      props: {
                        style: { display: "flex", alignItems: "center", justifyContent: "center", width: "150px", height: "150px", background: "#ffffff", borderRadius: "18px", overflow: "hidden", padding: "8px", boxSizing: "border-box", border: `2px solid ${t.accentDim}` },
                        children: [{ type: "img", props: { src: qrDataURI, style: { width: "100%", height: "100%" } } }],
                      },
                    },
                    {
                      type: "div",
                      props: {
                        style: { display: "flex", flexDirection: "column" },
                        children: [
                          { type: "div", props: { style: { fontSize: "13px", fontWeight: 500, color: t.textSec, fontFamily: FF, textTransform: "uppercase", letterSpacing: "1px", marginBottom: "6px" }, children: L.scanHint } },
                          { type: "div", props: { style: { fontSize: "16px", fontWeight: 400, color: t.accent, fontFamily: FF, opacity: 0.9 }, children: displayUrl } },
                        ],
                      },
                    },
                  ],
                },
              },
            ],
          },
        },
      ],
    },
  };
}

// ============================================================
//  LANDSCAPE LAYOUT
// ============================================================

function landscapeCard({ name, subtitle, displayUrl, qrDataURI }) {
  const t = theme;
  const cardW = canvasW - cardMargin * 2;
  const cardH = canvasH - cardMargin * 2;

  return {
    type: "div",
    props: {
      style: { display: "flex", width: "100%", height: "100%", background: t.bg, padding: `${cardMargin}px`, boxSizing: "border-box" },
      children: [{
        type: "div",
        props: {
          style: { display: "flex", flexDirection: "row", width: "100%", height: "100%", background: t.cardBg, borderRadius: "20px", overflow: "hidden", boxShadow: `0 8px 40px ${isDark ? "rgba(0,0,0,0.5)" : "rgba(0,0,0,0.08)"}` },
          children: [
            // Left: Logo preview
            { type: "div", props: { style: { display: "flex", alignItems: "center", justifyContent: "center", width: "52%", height: "100%", background: t.heroBg, padding: "32px", boxSizing: "border-box" }, children: [{ type: "div", props: { style: { display: "flex", width: "100%", height: "100%", background: isDark ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.02)", borderRadius: "14px", overflow: "hidden", alignItems: "center", justifyContent: "center" }, children: [{ type: "img", props: { src: logoURI, style: { maxWidth: "90%", maxHeight: "85%", objectFit: "contain" } } }] } }] } },
            // Right: Content
            { type: "div", props: { style: { display: "flex", flexDirection: "column", justifyContent: "center", width: "48%", height: "100%", padding: "40px 40px 40px 36px", boxSizing: "border-box" }, children: [
              { type: "div", props: { style: { width: "48px", height: "4px", background: t.accent, borderRadius: "2px", marginBottom: "24px" } } },
              ...(brand || platform ? [{ type: "div", props: { style: { fontSize: "13px", fontWeight: 600, color: t.textSec, fontFamily: FF, textTransform: "uppercase", letterSpacing: "3px", marginBottom: "14px" }, children: [brand, platform].filter(Boolean).join("  ·  ") } }] : []),
              { type: "div", props: { style: { fontSize: "46px", fontWeight: 700, color: t.text, fontFamily: FF, lineHeight: 1.15, marginBottom: "12px", letterSpacing: "-0.5px" }, children: name } },
              { type: "div", props: { style: { fontSize: "20px", fontWeight: 400, color: t.textSec, fontFamily: FF, lineHeight: 1.4, marginBottom: "28px" }, children: subtitle || L.defaultSubtitle } },
              { type: "div", props: { style: { width: "60%", height: "1px", background: t.divider, marginBottom: "28px" } } },
              { type: "div", props: { style: { display: "flex", flexDirection: "row", alignItems: "flex-start", gap: "16px", width: "100%" }, children: [
                { type: "div", props: { style: { display: "flex", flexDirection: "column", flex: 1 }, children: [
                  { type: "div", props: { style: { fontSize: "13px", fontWeight: 500, color: t.textSec, fontFamily: FF, textTransform: "uppercase", letterSpacing: "1px", marginBottom: "6px" }, children: L.scanHint } },
                  { type: "div", props: { style: { fontSize: "15px", fontWeight: 400, color: t.accent, fontFamily: FF, opacity: 0.9 }, children: displayUrl } },
                ] } },
                { type: "div", props: { style: { display: "flex", width: "100px", height: "100px", background: isDark ? "#1a1f2b" : "#f5f5f0", borderRadius: "12px", overflow: "hidden", alignItems: "center", justifyContent: "center", padding: "6px", boxSizing: "border-box", border: `2px solid ${t.divider}` }, children: [{ type: "img", props: { src: qrDataURI, style: { width: "100%", height: "100%" } } }] } },
              ] } },
            ] } },
          ],
        },
      }],
    },
  };
}

// ============================================================
//  MAIN
// ============================================================

async function main() {
  const qrDataURI = await generateQR(url);
  const displayUrl = url.replace("https://", "").replace("http://", "").replace(/\/$/, "");

  const layout = isSocial
    ? socialCard({ name, subtitle, displayUrl, qrDataURI, feature1, feature2, feature3 })
    : isSquare
    ? squareCard({ name, subtitle, displayUrl, qrDataURI })
    : landscapeCard({ name, subtitle, displayUrl, qrDataURI });

  const svg = await satori(layout, { width: canvasW, height: canvasH, fonts });
  const resvg = new Resvg(svg, { fitTo: { mode: "width", value: canvasW } });
  const pngBuffer = resvg.render().asPng();
  writeFileSync(outputPath, pngBuffer);
  console.log(`[OK] Card saved -> ${outputPath}  (theme: ${theme.name}, format: ${type}, renderer: satori, ${canvasW}x${canvasH})`);
}

main().catch((err) => { console.error("[ERROR]", err.message); process.exit(1); });
