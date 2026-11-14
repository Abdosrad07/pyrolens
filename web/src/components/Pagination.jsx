/**
 * Pagination - Pagination côté client pour les longues tables.
 * usePaged(items, pageSize) → { page, setPage, pageItems, total, totalPages, pageSize }
 * <Pagination {...page} onPageChange={page.setPage} />
 */
import { useMemo, useState } from "react";

export function usePaged(items, pageSize = 25) {
  const [page, setPage] = useState(0);
  const list = items || [];
  const total = list.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(page, totalPages - 1);
  const pageItems = useMemo(
    () => list.slice(safePage * pageSize, (safePage + 1) * pageSize),
    [list, safePage, pageSize]
  );
  return { page: safePage, setPage, pageItems, total, totalPages, pageSize };
}

export default function Pagination({ page, totalPages, total, pageSize, onPageChange }) {
  if (!totalPages || totalPages <= 1) return null;
  const from = page * pageSize + 1;
  const to = Math.min(total, (page + 1) * pageSize);
  return (
    <div className="pager">
      <span className="muted small">
        {from}–{to} sur {total}
      </span>
      <span style={{ flex: 1 }} />
      <button
        className="btn"
        disabled={page === 0}
        onClick={() => onPageChange(page - 1)}
      >
        ← Précédent
      </button>
      <span className="mono small">
        Page {page + 1} / {totalPages}
      </span>
      <button
        className="btn"
        disabled={page >= totalPages - 1}
        onClick={() => onPageChange(page + 1)}
      >
        Suivant →
      </button>
    </div>
  );
}
