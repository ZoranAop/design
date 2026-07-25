#!/usr/bin/env node
/**
 * Satori Card Generator
 * HTML/CSS → PNG shareable cards with QR code
 *
 * Usage:
 *   node generate.js --url https://example.com --name "Kimi K3" --image logo.png --theme tech
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
const subtitle = getArg("--subtitle") || "";
const outputPath = getArg("--output") || "card.png";

if (!url || !name || !imagePath) {
  console.log("Usage: node generate.js --url <URL> --name <Name> --image <path> [--theme tech] [--subtitle text] [--output card.png]");
  process.exit(1);
}

imagePath = resolve(imagePath);

// ============================================================
//  THEMES
// ============================================================

const THEMES = {
  minimal: {
    bg: "#faf9f5",
    cardBg: "#ffffff",
    text: "#141413",
    textSec: "#918c82",
    accent: "#8c9c76",
    divider: "#e8e6dc",
  },
  tech: {
    bg: "#080c14",
    cardBg: "#10151f",
    text: "#e6edf3",
    textSec: "#8b94a6",
    accent: "#58a6ff",
    divider: "#21262d",
  },
  organic: {
    bg: "#f8f4eb",
    cardBg: "#fffcf5",
    text: "#3a2e23",
    textSec: "#8d7962",
    accent: "#d97757",
    divider: "#e1d8c8",
  },
  bold: {
    bg: "#101010",
    cardBg: "#1a1a1a",
    text: "#faf9f5",
    textSec: "#b0aea5",
    accent: "#e67d50",
    divider: "#3a3834",
  },
};

const theme = THEMES[themeName] || THEMES.tech;
const canvasW = 1200;
const canvasH = 630;

// ============================================================
//  FONT LOADING (Windows system fonts)
// ============================================================

const fontDir = process.env.WINDIR + "/Fonts/";
function loadFont(file) {
  try {
    return readFileSync(fontDir + file);
  } catch {
    try {
      return readFileSync(file);
    } catch {
      console.warn(`Warning: font not found: ${file}`);
      return null;
    }
  }
}

const fonts = [];
const segoeUI = loadFont("segoeui.ttf");
const segoeUIBold = loadFont("segoeuib.ttf");
const simhei = loadFont("simhei.ttf");
const deng = loadFont("Deng.ttf");

if (segoeUI) fonts.push({ name: "Segoe UI", data: segoeUI, weight: 400, style: "normal" });
if (segoeUIBold) fonts.push({ name: "Segoe UI", data: segoeUIBold, weight: 700, style: "normal" });
if (simhei) fonts.push({ name: "SimHei", data: simhei, weight: 400, style: "normal" });
if (deng && !simhei) fonts.push({ name: "DengXian", data: deng, weight: 400, style: "normal" });

const fontFamily = `"Segoe UI", "SimHei", "DengXian", Arial, sans-serif`;
const fontFamilyMono = `"Cascadia Code", "Consolas", monospace`;

// ============================================================
//  IMAGE LOADING
// ============================================================

function loadImageAsDataURI(filePath, maxW, maxH) {
  // For satori, we can use the file path directly with file:// protocol
  // Or we can read and convert to base64
  try {
    const buf = readFileSync(filePath);
    const ext = basename(filePath).split(".").pop().toLowerCase();
    const mime = ext === "png" ? "image/png" : ext === "jpg" || ext === "jpeg" ? "image/jpeg" : "image/png";
    return `data:${mime};base64,${buf.toString("base64")}`;
  } catch (e) {
    console.error(`Cannot read image: ${filePath}`);
    process.exit(1);
  }
}

const uiImageDataURI = loadImageAsDataURI(imagePath);

// ============================================================
//  QR CODE
// ============================================================

async function generateQR(url) {
  const dataURI = await QRCode.toDataURL(url, {
    width: 300,
    margin: 2,
    color: { dark: "#000000", light: "#ffffff" },
  });
  return dataURI;
}

// ============================================================
//  CARD LAYOUT (JSX-style object)
// ============================================================

function cardLayout({ name, subtitle, displayUrl, qrDataURI, theme }) {
  const isDark = theme.text === "#e6edf3" || theme.text === "#faf9f5";
  const qrFill = isDark ? "#ffffff" : "#000000";
  const qrBg = isDark ? "#1a1f2b" : "#f5f5f0";

  return {
    type: "div",
    props: {
      style: {
        display: "flex",
        width: "100%",
        height: "100%",
        background: theme.bg,
        padding: "24px",
        boxSizing: "border-box",
      },
      children: [
        // Card container
        {
          type: "div",
          props: {
            style: {
              display: "flex",
              flexDirection: "row",
              width: "100%",
              height: "100%",
              background: theme.cardBg,
              borderRadius: "20px",
              overflow: "hidden",
              boxShadow: `0 8px 40px ${isDark ? "rgba(0,0,0,0.5)" : "rgba(0,0,0,0.08)"}`,
            },
            children: [
              // Left: UI preview
              {
                type: "div",
                props: {
                  style: {
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    width: "52%",
                    height: "100%",
                    background: isDark ? "#0a0d14" : "#f0efe9",
                    padding: "32px",
                    boxSizing: "border-box",
                  },
                  children: [
                    {
                      type: "div",
                      props: {
                        style: {
                          display: "flex",
                          width: "100%",
                          height: "100%",
                          background: isDark ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.02)",
                          borderRadius: "14px",
                          overflow: "hidden",
                          alignItems: "center",
                          justifyContent: "center",
                        },
                        children: [
                          {
                            type: "img",
                            props: {
                              src: uiImageDataURI,
                              style: {
                                maxWidth: "90%",
                                maxHeight: "85%",
                                objectFit: "contain",
                              },
                            },
                          },
                        ],
                      },
                    },
                  ],
                },
              },
              // Right: content
              {
                type: "div",
                props: {
                  style: {
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "center",
                    width: "48%",
                    height: "100%",
                    padding: "40px 40px 40px 36px",
                    boxSizing: "border-box",
                  },
                  children: [
                    // Accent line
                    {
                      type: "div",
                      props: {
                        style: {
                          width: "48px",
                          height: "4px",
                          background: theme.accent,
                          borderRadius: "2px",
                          marginBottom: "24px",
                        },
                      },
                    },
                    // Model name
                    {
                      type: "div",
                      props: {
                        style: {
                          fontSize: "46px",
                          fontWeight: 700,
                          color: theme.text,
                          fontFamily,
                          lineHeight: 1.15,
                          marginBottom: subtitle ? "12px" : "28px",
                          letterSpacing: "-0.5px",
                        },
                        children: name,
                      },
                    },
                    // Subtitle
                    ...(subtitle
                      ? [
                          {
                            type: "div",
                            props: {
                              style: {
                                fontSize: "20px",
                                fontWeight: 400,
                                color: theme.textSec,
                                fontFamily,
                                lineHeight: 1.4,
                                marginBottom: "28px",
                              },
                              children: subtitle,
                            },
                          },
                        ]
                      : []),
                    // Divider
                    {
                      type: "div",
                      props: {
                        style: {
                          width: "60%",
                          height: "1px",
                          background: theme.divider,
                          marginBottom: "28px",
                        },
                      },
                    },
                    // URL row
                    {
                      type: "div",
                      props: {
                        style: {
                          display: "flex",
                          flexDirection: "row",
                          alignItems: "flex-start",
                          gap: "16px",
                          width: "100%",
                        },
                        children: [
                          {
                            type: "div",
                            props: {
                              style: {
                                display: "flex",
                                flexDirection: "column",
                                flex: 1,
                              },
                              children: [
                                {
                                  type: "div",
                                  props: {
                                    style: {
                                      fontSize: "13px",
                                      fontWeight: 500,
                                      color: theme.textSec,
                                      fontFamily,
                                      textTransform: "uppercase",
                                      letterSpacing: "1px",
                                      marginBottom: "6px",
                                    },
                                    children: "Scan to visit",
                                  },
                                },
                                {
                                  type: "div",
                                  props: {
                                    style: {
                                      fontSize: "15px",
                                      fontWeight: 400,
                                      color: theme.accent,
                                      fontFamily: fontFamilyMono,
                                      opacity: 0.9,
                                    },
                                    children: displayUrl,
                                  },
                                },
                              ],
                            },
                          },
                          // QR code
                          {
                            type: "div",
                            props: {
                              style: {
                                display: "flex",
                                width: "100px",
                                height: "100px",
                                background: qrBg,
                                borderRadius: "12px",
                                overflow: "hidden",
                                alignItems: "center",
                                justifyContent: "center",
                                padding: "6px",
                                boxSizing: "border-box",
                                border: `2px solid ${theme.divider}`,
                              },
                              children: [
                                {
                                  type: "img",
                                  props: {
                                    src: qrDataURI,
                                    style: {
                                      width: "100%",
                                      height: "100%",
                                    },
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
        },
      ],
    },
  };
}

// ============================================================
//  MAIN
// ============================================================

async function main() {
  console.log(`Generating card...`);
  console.log(`  URL:    ${url}`);
  console.log(`  Name:   ${name}`);
  console.log(`  Theme:  ${themeName}`);
  console.log(`  Image:  ${imagePath}`);

  const qrDataURI = await generateQR(url);
  const displayUrl = url.replace("https://", "").replace("http://", "").replace(/\/$/, "");

  const layout = cardLayout({ name, subtitle, displayUrl, qrDataURI, theme });

  console.log("  Rendering SVG via Satori...");
  const svg = await satori(layout, {
    width: canvasW,
    height: canvasH,
    fonts,
  });

  console.log("  Converting SVG → PNG via resvg...");
  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: canvasW },
  });
  const pngData = resvg.render();
  const pngBuffer = pngData.asPng();

  writeFileSync(outputPath, pngBuffer);
  console.log(`\n  ✓ Card saved → ${outputPath}`);
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
