import React, { Fragment, ReactNode } from "react";

export function renderHighlighted(snippet: string, ranges: [number, number][]): ReactNode[] {
  if (!ranges || ranges.length === 0) return [snippet];
  const sorted = [...ranges].sort((a,b)=> a[0]-b[0]).reduce<[number, number][]>((acc, r) => {
    if (acc.length === 0) return [r];
    const last = acc[acc.length-1];
    if (r[0] <= last[1]) { last[1] = Math.max(last[1], r[1]); return acc; }
    acc.push(r); return acc;
  }, []);
  const out: ReactNode[] = [];
  let pos = 0;
  sorted.forEach((r, idx) => {
    const [s,e] = r;
    if (s > pos) out.push(<Fragment key={`p${idx}-pre`}>{snippet.slice(pos, s)}</Fragment>);
    out.push(<mark key={`m${idx}`} className="bg-yellow-200 rounded px-0.5">{snippet.slice(s,e)}</mark>);
    pos = e;
  });
  if (pos < snippet.length) out.push(<Fragment key="post">{snippet.slice(pos)}</Fragment>);
  return out;
}
