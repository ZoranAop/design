#!/usr/bin/env node
/**
 * Satori Card Generator
 * HTML/CSS → PNG shareable cards with QR code
 *
 * Usage (landscape card):
 *   node generate.js --url https://example.com --name "Kimi K3" --image logo.png
 *
 * Usage (social portrait card):
 *   node generate.js --url https://example.com --name "Kimi K3" --image logo.png --type social --subtitle "新一代 AI 模型"
 */

import { readFileSync, writeFileSync } from "fs";
import { resolve, basename } from "path";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import QRCode from "qrcode";

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
const themeName = getArg("--theme") || "tech";
const type = getArg("--type") || "landscape";
const subtitle = getArg("--subtitle") || "";
const feature1 = getArg("--f1") || "";
const feature2 = getArg("--f2") || "";
const feature3 = getArg("--f3") || "";
const outputPath = getArg("--output") || "card.png";

if (!url || !name || !imagePath) {
  console.log("Usage: node generate.js --url <URL> --name <Name> --image <path> [--type social] [--theme tech] [--subtitle text] [--f1 feature] [--f2 feature] [--f3 feature] [--output card.png]");
  process.exit(1);
}

imagePath = resolve(imagePath);

// ============================================================
//  THEMES
// ============================================================

const THEMES = {
  minimal: {
    bg: "#f3f2ee", cardBg: "#ffffff", heroBg: "#eae8e2",
    text: "#1a1a18", textSec: "#8a857a", accent: "#8c9c76", accentDim: "#b4c4a0",
    divider: "#e0ded7",
  },
  tech: {
    bg: "#06080e", cardBg: "#0e121c", heroBg: "#0a0e18",
    text: "#e8eef5", textSec: "#7d8699", accent: "#4da6ff", accentDim: "#2a5a8c",
    divider: "#1e2433",
  },
  organic: {
    bg: "#f0e8d8", cardBg: "#faf5ea", heroBg: "#ece0c8",
    text: "#3d2e20", textSec: "#8a7055", accent: "#d97757", accentDim: "#c46a4a",
    divider: "#e0d4c0",
  },
  bold: {
    bg: "#0a0a0a", cardBg: "#181818", heroBg: "#121212",
    text: "#faf9f5", textSec: "#a09c93", accent: "#e87d50", accentDim: "#b55a36",
    divider: "#2e2c28",
  },
};

const theme = THEMES[themeName] || THEMES.tech;
const isDark = themeName === "tech" || themeName === "bold";
const isSocial = type === "social";

const canvasW = isSocial ? 800 : 1200;
const canvasH = isSocial ? 1280 : 630;
const cardMargin = isSocial ? 20 : 24;

// ============================================================
//  FONT LOADING
// ============================================================

const fontDir = process.env.WINDIR + "/Fonts/";
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
  if (features.length === 0) features.push("AI 对话助手", "多模态理解", "实时联网搜索");

  const cardW = canvasW - cardMargin * 2;
  const innerPad = 40;

  return {
    type: "div",
    props: {
      style: {
        display: "flex", width: "100%", height: "100%",
        background: t.bg, padding: `${cardMargin}px`, boxSizing: "border-box",
        alignItems: "center", justifyContent: "center",
      },
      children: [
        // Card
        {
          type: "div",
          props: {
            style: {
              display: "flex", flexDirection: "column",
              width: `${cardW}px`, height: `${canvasH - cardMargin * 2}px`,
              background: t.cardBg, borderRadius: "24px", overflow: "hidden",
              boxShadow: `0 12px 60px ${isDark ? "rgba(0,0,0,0.6)" : "rgba(0,0,0,0.10)"}`,
            },
            children: [
              // --- Hero section with logo ---
              {
                type: "div",
                props: {
                  style: {
                    display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center",
                    width: "100%", height: "40%",
                    background: `linear-gradient(180deg, ${t.heroBg} 0%, ${t.cardBg} 100%)`,
                    padding: "40px 40px 20px 40px", boxSizing: "border-box",
                  },
                  children: [
                    // Subtle top line
                    {
                      type: "div",
                      props: {
                        style: {
                          width: "60px", height: "3px",
                          background: t.accent, borderRadius: "2px",
                          marginBottom: "40px",
                        },
                      },
                    },
                    // Logo container
                    {
                      type: "div",
                      props: {
                        style: {
                          display: "flex", alignItems: "center", justifyContent: "center",
                          width: "180px", height: "180px",
                          background: isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)",
                          borderRadius: "40px",
                          padding: "28px", boxSizing: "border-box",
                          border: `1px solid ${t.divider}`,
                        },
                        children: [
                          {
                            type: "img",
                            props: {
                              src: logoURI,
                              style: { maxWidth: "100%", maxHeight: "100%", objectFit: "contain" },
                            },
                          },
                        ],
                      },
                    },
                    // Platform name label
                    {
                      type: "div",
                      props: {
                        style: {
                          fontSize: "14px", fontWeight: 500, color: t.textSec, fontFamily: FF,
                          textTransform: "uppercase", letterSpacing: "3px",
                          marginTop: "24px",
                        },
                        children: "O P E  ·  A I  P l a t f o r m",
                      },
                    },
                  ],
                },
              },
              // --- Content section ---
              {
                type: "div",
                props: {
                  style: {
                    display: "flex", flexDirection: "column", alignItems: "center",
                    width: "100%", flex: 1,
                    padding: `0 ${innerPad}px ${innerPad}px ${innerPad}px`,
                    boxSizing: "border-box",
                  },
                  children: [
                    // NEW badge
                    {
                      type: "div",
                      props: {
                        style: {
                          display: "flex", alignItems: "center", justifyContent: "center",
                          padding: "6px 18px", background: t.accent,
                          borderRadius: "20px", marginBottom: "16px",
                        },
                        children: [
                          {
                            type: "div",
                            props: {
                              style: { fontSize: "13px", fontWeight: 700, color: "#ffffff", fontFamily: FF, letterSpacing: "1px" },
                              children: "N E W  ·  新 品 上 线",
                            },
                          },
                        ],
                      },
                    },
                    // Model name
                    {
                      type: "div",
                      props: {
                        style: {
                          fontSize: "52px", fontWeight: 700, color: t.text, fontFamily: FF,
                          lineHeight: 1.1, letterSpacing: "-1px", textAlign: "center",
                        },
                        children: name,
                      },
                    },
                    // Subtitle
                    ...(subtitle ? [{
                      type: "div",
                      props: {
                        style: {
                          fontSize: "20px", fontWeight: 400, color: t.textSec, fontFamily: FF,
                          marginTop: "12px", textAlign: "center",
                        },
                        children: subtitle,
                      },
                    }] : []),
                    // Divider
                    {
                      type: "div",
                      props: {
                        style: {
                          width: "80px", height: "2px", background: t.divider,
                          marginTop: "28px", marginBottom: "28px",
                        },
                      },
                    },
                    // Features
                    ...features.map((f, i) => ({
                      type: "div",
                      props: {
                        style: {
                          display: "flex", flexDirection: "row", alignItems: "center",
                          width: "100%", justifyContent: "center",
                          marginBottom: i < features.length - 1 ? "10px" : "0",
                        },
                        children: [
                          {
                            type: "div",
                            props: {
                              style: {
                                width: "6px", height: "6px", borderRadius: "3px",
                                background: t.accent, marginRight: "12px", flexShrink: 0,
                              },
                            },
                          },
                          {
                            type: "div",
                            props: {
                              style: { fontSize: "16px", fontWeight: 400, color: t.textSec, fontFamily: FF },
                              children: f,
                            },
                          },
                        ],
                      },
                    })),
                    // Spacer
                    { type: "div", props: { style: { flex: 1 } } },
                    // QR section
                    {
                      type: "div",
                      props: {
                        style: {
                          display: "flex", flexDirection: "column", alignItems: "center",
                          width: "100%", marginTop: "20px",
                        },
                        children: [
                          // Thin rule
                          {
                            type: "div",
                            props: {
                              style: {
                                width: "100%", height: "1px",
                                background: `linear-gradient(90deg, transparent 0%, ${t.divider} 50%, transparent 100%)`,
                                marginBottom: "24px",
                              },
                            },
                          },
                          // CTA text
                          {
                            type: "div",
                            props: {
                              style: { fontSize: "14px", fontWeight: 500, color: t.textSec, fontFamily: FF, letterSpacing: "1px", marginBottom: "12px" },
                              children: "扫 码 立 即 体 验",
                            },
                          },
                          // QR code frame
                          {
                            type: "div",
                            props: {
                              style: {
                                display: "flex", alignItems: "center", justifyContent: "center",
                                width: "140px", height: "140px",
                                background: "#ffffff", borderRadius: "18px",
                                overflow: "hidden", padding: "8px", boxSizing: "border-box",
                                border: `2px solid ${t.accentDim}`,
                              },
                              children: [
                                {
                                  type: "img",
                                  props: { src: qrDataURI, style: { width: "100%", height: "100%" } },
                                },
                              ],
                            },
                          },
                          // URL text
                          {
                            type: "div",
                            props: {
                              style: { fontSize: "13px", fontWeight: 400, color: t.accent, fontFamily: FF, marginTop: "12px", opacity: 0.85 },
                              children: displayUrl,
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
        },
      ],
    },
  };
}

// ============================================================
//  LANDSCAPE LAYOUT (original)
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
              { type: "div", props: { style: { fontSize: "46px", fontWeight: 700, color: t.text, fontFamily: FF, lineHeight: 1.15, marginBottom: subtitle ? "12px" : "28px", letterSpacing: "-0.5px" }, children: name } },
              ...(subtitle ? [{ type: "div", props: { style: { fontSize: "20px", fontWeight: 400, color: t.textSec, fontFamily: FF, lineHeight: 1.4, marginBottom: "28px" }, children: subtitle } }] : []),
              { type: "div", props: { style: { width: "60%", height: "1px", background: t.divider, marginBottom: "28px" } } },
              { type: "div", props: { style: { display: "flex", flexDirection: "row", alignItems: "flex-start", gap: "16px", width: "100%" }, children: [
                { type: "div", props: { style: { display: "flex", flexDirection: "column", flex: 1 }, children: [
                  { type: "div", props: { style: { fontSize: "13px", fontWeight: 500, color: t.textSec, fontFamily: FF, textTransform: "uppercase", letterSpacing: "1px", marginBottom: "6px" }, children: "Scan to visit" } },
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
  console.log(`Generating ${isSocial ? "SOCIAL" : "LANDSCAPE"} card...`);
  console.log(`  URL:   ${url}`);
  console.log(`  Name:  ${name}`);
  console.log(`  Theme: ${themeName}`);
  console.log(`  Image: ${imagePath}`);

  const qrDataURI = await generateQR(url);
  const displayUrl = url.replace("https://", "").replace("http://", "").replace(/\/$/, "");

  const layout = isSocial
    ? socialCard({ name, subtitle, displayUrl, qrDataURI, feature1, feature2, feature3 })
    : landscapeCard({ name, subtitle, displayUrl, qrDataURI });

  console.log("  Rendering SVG via Satori...");
  const svg = await satori(layout, { width: canvasW, height: canvasH, fonts });

  console.log("  Converting SVG → PNG via resvg...");
  const resvg = new Resvg(svg, { fitTo: { mode: "width", value: canvasW } });
  const pngBuffer = resvg.render().asPng();
  writeFileSync(outputPath, pngBuffer);
  console.log(`\n  ✓ Card saved → ${outputPath}  (${canvasW}x${canvasH})`);
}

main().catch((err) => { console.error("Error:", err); process.exit(1); });
