import { useRef, useEffect, useMemo } from 'react';
import * as uPlot from 'uplot';
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

  const opts = useMemo(() => ({
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
      y: { range: (u: uPlot, dataMin: number, dataMax: number) => [dataMin * 0.98, dataMax * 1.02] },
    },
    cursor: { show: false },
    hooks: {
      draw: [
        (u: uPlot) => {
          // Draw current value indicator
          const { ctx, series, scales, bbox } = u;
          const lastIdx = series[1].data.length - 1;
          const x = u.valToPos(lastIdx, 'x', true);
          const y = u.valToPos(series[1].data[lastIdx], 'y', true);
          
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
  }), [color, height, width, showArea, strokeWidth]);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const series = [
      data.map(d => new Date(d.t).getTime()),
      data.map(d => d.y),
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
      {icons[trend]} {value > 0 ? '+' : ''}{value.toFixed(1)}%
    </span>
  );
}