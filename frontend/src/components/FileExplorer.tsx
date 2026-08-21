import { useEffect, useState } from "react";
import { fetchTree, formatBytes, readFile, type FileEntry } from "../api";

export function FileExplorer({
  workspace,
  onOpenFile,
}: {
  workspace: string;
  onOpenFile?: (path: string, content: string) => void;
}) {
  const [relative, setRelative] = useState(".");
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [previewPath, setPreviewPath] = useState<string | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!workspace) return;
      setLoading(true);
      setError(null);
      try {
        const data = await fetchTree(workspace, relative);
        if (!cancelled) setEntries(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Erro ao listar");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [workspace, relative]);

  async function openEntry(entry: FileEntry) {
    if (entry.is_dir) {
      setRelative(entry.path);
      setPreviewPath(null);
      setPreview("");
      return;
    }
    try {
      const content = await readFile(workspace, entry.path);
      setPreviewPath(entry.path);
      setPreview(content.slice(0, 12000));
      onOpenFile?.(entry.path, content);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao ler arquivo");
    }
  }

  function goUp() {
    if (relative === "." || !relative) return;
    const parts = relative.split("/").filter(Boolean);
    parts.pop();
    setRelative(parts.length ? parts.join("/") : ".");
  }

  return (
    <div className="files-panel">
      <div className="files-header">
        <h2>Arquivos do projeto</h2>
        <p>{workspace}</p>
      </div>

      <div style={{ padding: "0.5rem 0.65rem 0", display: "flex", gap: "0.4rem" }}>
        <button type="button" className="ghost-btn" onClick={goUp} disabled={relative === "."}>
          ↑ Subir
        </button>
        <button
          type="button"
          className="ghost-btn"
          onClick={() => setRelative(".")}
          disabled={relative === "."}
        >
          Raiz
        </button>
      </div>

      <div className="file-list">
        {loading && <div className="empty-files">Carregando…</div>}
        {error && <div className="empty-files">{error}</div>}
        {!loading && !error && entries.length === 0 && (
          <div className="empty-files">Pasta vazia. Peça ao agente para criar arquivos.</div>
        )}
        {!loading &&
          entries.map((entry) => (
            <button
              key={entry.path}
              type="button"
              className={`file-item ${previewPath === entry.path ? "active" : ""}`}
              onClick={() => void openEntry(entry)}
            >
              <span className="file-icon">{entry.is_dir ? "[dir]" : "[file]"}</span>
              <span className="file-name">{entry.name}</span>
              {!entry.is_dir && <span className="file-size">{formatBytes(entry.size)}</span>}
            </button>
          ))}
      </div>

      {previewPath && (
        <div className="preview">
          <div className="preview-title">{previewPath}</div>
          <pre>{preview}</pre>
        </div>
      )}
    </div>
  );
}
