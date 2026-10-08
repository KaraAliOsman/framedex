import type { SVGProps } from "react";
import { wordmarkGeometry } from "./wordmarkGeometry";
import "./brand.css";

type MarkProps = Omit<SVGProps<SVGSVGElement>, "width" | "height"> & {
  size?: number;
  title?: string;
};

function SectionGeometry({ optical = false }: { optical?: boolean }): JSX.Element {
  return (
    <>
      <path
        fillRule="evenodd"
        d={`M2 0H22Q24 0 24 2V22Q24 24 22 24H2Q0 24 0 22V2Q0 0 2 0Z${optical ? "M3 3V21H21V3Z" : "M2.5 2.5V21.5H21.5V2.5Z"}`}
      />
      <path d={optical ? "M6.875 3H9.125V21H6.875Z" : "M7 2.5H9V21.5H7Z"} />
    </>
  );
}

export function BrandMark({ size = 24, title, className = "", ...props }: MarkProps): JSX.Element {
  const actualSize = Math.max(16, size);
  return (
    <svg
      {...props}
      className={`brand-mark ${className}`}
      viewBox="0 0 24 24"
      width={actualSize}
      height={actualSize}
      role={title ? "img" : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      <SectionGeometry optical={actualSize < 24} />
    </svg>
  );
}

function WordmarkGeometry(): JSX.Element {
  const { paths, scale, markX } = wordmarkGeometry;
  return (
    <>
      {paths.map(({ d, x }, index) => (
        <path key={index} d={d} transform={`translate(${x} 24) scale(${scale} ${-scale})`} />
      ))}
      <g transform={`translate(${markX} 0)`}>
        <SectionGeometry />
      </g>
    </>
  );
}

export function Wordmark({ width = 144 }: { width?: number }): JSX.Element {
  const actualWidth = Math.max(72, width);
  return (
    <svg
      className="brand-wordmark"
      viewBox={`0 0 ${wordmarkGeometry.width} 24`}
      width={actualWidth}
      height={(actualWidth * 24) / wordmarkGeometry.width}
      role="img"
      aria-label="DEKOPEN"
    >
      <WordmarkGeometry />
    </svg>
  );
}

export function DocLockup({ width = 176 }: { width?: number }): JSX.Element {
  const fullWidth = wordmarkGeometry.width + 8;
  return (
    <svg
      className="brand-lockup"
      viewBox={`0 0 ${fullWidth} 44`}
      width={Math.max(80, width)}
      height={(Math.max(80, width) * 44) / fullWidth}
      role="img"
      aria-label="DEKOPEN"
    >
      <g transform="translate(4 4)">
        <WordmarkGeometry />
      </g>
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="0.75"
        d={`M4 32V40M${fullWidth - 4} 32V40M4 36H${fullWidth - 4}M1 39L7 33M${fullWidth - 7} 39L${fullWidth - 1} 33`}
      />
    </svg>
  );
}
