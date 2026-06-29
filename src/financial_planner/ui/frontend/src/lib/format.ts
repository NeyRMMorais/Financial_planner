export const fmtCurrency = (val: any, mode: "USD" | "LC" = "USD") => {
  if (val === null || val === undefined || val === "") return mode === "USD" ? "$ —" : "LC —";
  const n = Number(val);
  if (Number.isNaN(n)) return mode === "USD" ? "$ —" : "LC —";
  const prefix = mode === "USD" ? "$ " : "LC ";
  return prefix + Math.round(n).toLocaleString("en-US");
};

export const fmtNumber = (val: any, digits = 0) => {
  if (val === null || val === undefined || val === "") return "—";
  const n = Number(val);
  if (Number.isNaN(n)) return "—";
  return n.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
};

export const fmtVolume = (val: any) => {
  if (val === null || val === undefined || val === "") return "— MT";
  const n = Number(val);
  if (Number.isNaN(n)) return "— MT";
  return n.toLocaleString("en-US", { minimumFractionDigits: 3, maximumFractionDigits: 3 }) + " MT";
};

export const fmtPriceUnit = (val: any, mode: "USD" | "LC" = "USD") => {
  if (val === null || val === undefined || val === "") return mode === "USD" ? "$ —" : "LC —";
  const n = Number(val);
  if (Number.isNaN(n)) return mode === "USD" ? "$ —" : "LC —";
  const prefix = mode === "USD" ? "$ " : "LC ";
  return prefix + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};
