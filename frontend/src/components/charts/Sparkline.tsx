import { useRef, useEffect, useMemo } from 'react';
import uPlot, { type Options } from 'uplot';
import { cn } from '@utils/cn';

interface SparklineProps {
  data: Array<{ t: string | number; y: number }>;
  color?: string;
  height?: number;
  width?: number;
  showArea?: boolean;
  strokeWidth?: number;
}

export function Sparkline({
  data,
  color = 'var(--chart-1)',
  height = 60,
  width,
  showArea = false,
  strokeWidth = 2,
}: SparklineProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const uplotRef = useRef<uPlot | null>(null);

  const opts = useMemo(
    (): Options => ({
      width: width || 300,
      height,
      title: '',
      axes: [
        { show: false }, // x
        { show: false }, // y
      ],
      series: [
        {}, // x
        {
          label: 'Value',
          stroke: color,
          fill: showArea ? `${color}20` : 'none',
          width: strokeWidth,
          points: { show: false },
        },
      ],
      scales: {
        x: { time: false },
        y: {
          range: (_u: uPlot, dataMin: number, dataMax: number) =>
            [dataMin * 0.98, dataMax * 1.02] as const,
        },
      },
      cursor: { show: false },
      hooks: {
        draw: [
          (u: uPlot) => {
            // Draw current value indicator
            const { ctx, series, scales, bbox } = u;
            const ySeries = series[1];
            // Access series data via u.series or direct access
            const yData =
              (ySeries as { data?: Float64Array | number[] }).data ??
              (u.series[1] as { data?: Float64Array | number[] }).data;
            const yDataArray = (yData as Float64Array | number[]) ?? [];
            const lastIdx = yDataArray.length - 1;
            const x = u.valToPos(lastIdx, 'x', true);
            const y = u.valToPos(yDataArray[lastIdx], 'y', true);

            ctx.save();
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.restore();
          },
        ],
      },
    }),
    [color, height, width, showArea, strokeWidth]
  );

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const series: [Float64Array, Float64Array] = [
      new Float64Array(data.map(d => new Date(d.t).getTime())),
      new Float64Array(data.map(d => d.y)),
    ];

    uplotRef.current = new uPlot(opts, series, containerRef.current);

    return () => {
      uplotRef.current?.destroy();
      uplotRef.current = null;
    };
  }, [data, opts]);

  return (
    <div
      ref={containerRef}
      className={cn('sparkline-container', 'w-full')}
      style={{ width: width || '100%', height }}
      role="img"
      aria-label={`Sparkline chart with ${data.length} data points`}
    />
  );
}

// Mini trend indicator for inline use
interface MiniTrendProps {
  trend: 'up' | 'down' | 'stable';
  value: number;
  color?: string;
}

export function MiniTrend({ trend, value, color }: MiniTrendProps) {
  const colors = {
    up: 'text-success',
    down: 'text-critical',
    stable: 'text-text-muted',
  };

  const icons = {
    up: '▲',
    down: '▼',
    stable: '●',
  };

  return (
    <span className={cn('flex items-center gap-1 text-caption font-medium', colors[trend], color)}>
      {icons[trend]} {value > 0 ? '+' : ''}
      {value.toFixed(1)}%
    </span>
  );
}
