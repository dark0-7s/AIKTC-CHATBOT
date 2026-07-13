const PALETTES = [
  { bg: "#E1F5EE", color: "#0F6E56" },
  { bg: "#EEEDFE", color: "#534AB7" },
  { bg: "#E6F1FB", color: "#185FA5" },
  { bg: "#FAECE7", color: "#993C1D" },
  { bg: "#FAEEDA", color: "#854F0B" },
  { bg: "#FBEAF0", color: "#993556" },
  { bg: "#EAF3DE", color: "#3B6D11" },
  { bg: "#F1EFE8", color: "#5F5E5A" },
];

export function avatarPalette(initials) {
  const s = (initials || "AA").padEnd(2, "A");
  return PALETTES[(s.charCodeAt(0) + s.charCodeAt(1)) % PALETTES.length];
}
