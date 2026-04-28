export type LocalPreview = {
  columns: string[];
  rows: Record<string, string>[];
};

export const parseLocalPreview = async (file: File): Promise<LocalPreview | null> => {
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (extension === "csv") {
    const text = await readFileText(file);
    const lines = text.split(/\r?\n/).filter(Boolean).slice(0, 6);
    const [header, ...rows] = lines;
    if (!header) {
      return null;
    }
    const columns = header.split(",").map((item) => item.trim());
    return {
      columns,
      rows: rows.map((line) => {
        const values = line.split(",");
        return columns.reduce<Record<string, string>>((accumulator, column, index) => {
          accumulator[column] = values[index]?.trim() ?? "";
          return accumulator;
        }, {});
      }),
    };
  }
  if (extension === "json") {
    const text = await readFileText(file);
    const parsed = JSON.parse(text) as unknown;
    if (!Array.isArray(parsed) || parsed.length === 0 || typeof parsed[0] !== "object" || parsed[0] === null) {
      return null;
    }
    const rows = parsed.slice(0, 5) as Record<string, string | number | boolean | null>[];
    const columns = Object.keys(rows[0]);
    return {
      columns,
      rows: rows.map((row) =>
        columns.reduce<Record<string, string>>((accumulator, column) => {
          accumulator[column] = String(row[column] ?? "");
          return accumulator;
        }, {}),
      ),
    };
  }
  return null;
};

const readFileText = async (file: File): Promise<string> => {
  if (typeof file.text === "function") {
    return file.text();
  }
  return new Response(file).text();
};
