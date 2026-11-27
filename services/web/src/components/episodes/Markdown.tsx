import { Fragment } from "react";

const INLINE = /(\*\*[^*]+\*\*|<https?:\/\/[^>\s]+>|\[[^\]]+\]\(https?:\/\/[^)\s]+\)|\*[^*]+\*)/g;

function inline(text: string): React.ReactNode[] {
  return text.split(INLINE).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
    const auto = /^<(https?:\/\/[^>\s]+)>$/.exec(part);
    if (auto)
      return (
        <a key={i} href={auto[1]} target="_blank" rel="noopener noreferrer">
          {auto[1]}
        </a>
      );
    const link = /^\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)$/.exec(part);
    if (link)
      return (
        <a key={i} href={link[2]} target="_blank" rel="noopener noreferrer">
          {link[1]}
        </a>
      );
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) return <em key={i}>{part.slice(1, -1)}</em>;
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export function Markdown({ source }: { source: string }) {
  const blocks: React.ReactNode[] = [];
  let para: string[] = [];
  let list: string[] = [];
  const flush = () => {
    if (para.length) blocks.push(<p key={blocks.length}>{para.map((l, i) => <Fragment key={i}>{i > 0 && <br />}{inline(l)}</Fragment>)}</p>);
    if (list.length) blocks.push(<ul key={blocks.length}>{list.map((l, i) => <li key={i}>{inline(l)}</li>)}</ul>);
    para = [];
    list = [];
  };
  for (const raw of source.split("\n")) {
    const line = raw.trim();
    const heading = /^(#{1,3})\s+(.*)$/.exec(line);
    if (heading) {
      flush();
      const level = heading[1].length;
      blocks.push(level === 1 ? <h2 key={blocks.length}>{inline(heading[2])}</h2> : <h3 key={blocks.length}>{inline(heading[2])}</h3>);
    } else if (line.startsWith("- ")) {
      if (para.length) flush();
      list.push(line.slice(2));
    } else if (line === "") flush();
    else {
      if (list.length) flush();
      para.push(line);
    }
  }
  flush();
  return <div className="prose-news">{blocks}</div>;
}
