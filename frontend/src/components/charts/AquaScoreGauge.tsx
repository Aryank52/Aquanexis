import { useEffect, useRef, useMemo } from 'react';
import { cn } from '@utils/cn';

interface GaugeProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  showValue?: boolean;
  animate?: boolean;
  bands?: Array<{ min: number; max: number; color: string }>;
}

const defaultBands = [
  { min: 0, max: 39, color: '#dc2626' },    // Critical - red
  { min: 40, max: 69, color: '#d97706' },   // Warning - amber
  { min: 70, max: 100, color: '#059669' },  // Good - green
];

export function AquaScoreGauge({
  value,
  max = 100,
  size = 200,
  strokeWidth = 16,
  label = 'AquaScore',
  showValue = true,
  animate = true,
  bands = defaultBands,
}: GaugeProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const pathRef = useRef<SVGCircleElement>(null);
  const prevValueRef = useRef(value);

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedValue = Math.max(0, Math.min(max, value));
  const progress = clampedValue / max;
  const offset = circumference * (1 - progress);

  // Calculate band paths
  const bandPaths = useMemo(() => {
    return bands.map((band) => {
      const startAngle = (band.min / max) * 360 - 90;
      const endAngle = (band.max / max) * 360 - 90;
      const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0;
      
      const startRad = (startAngle * Math.PI) / 180;
      const endRad = (endAngle * Math.PI) / 180;
      
      const x1 = size / 2 + radius * Math.cos(startRad);
      const y1 = size / 2 + radius * Math.sin(startRad);
      const x2 = size / 2 + radius * Math.cos(endRad);
      const y2 = size / 2 + radius * Math.sin(endRad);
      
      return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`;
    });
  }, [bands, max, radius, size]);

  // Animate value change
  useEffect(() => {
    if (!animate || !pathRef.current) return;
    
    const path = pathRef.current;
    const startOffset = circumference * (1 - prevValueRef.current / max);
    const endOffset = offset;
    
    // Use CSS animation for smooth transition
    path.style.transition = 'stroke-dashoffset 600ms ease-out';
    path.style.strokeDashoffset = `${endOffset}`;
    
    prevValueRef.current = value;
  }, [value, max, circumference, animate, offset]);

  // Initial animation on mount
  useEffect(() => {
    if (!animate || !pathRef.current) return;
    
    const path = pathRef.current;
    path.style.strokeDashoffset = `${circumference}`;
    path.style.transition = 'none';
    
    // Force reflow
    path.getBoundingClientRect();
    
    path.style.transition = 'stroke-dashoffset 800ms ease-out';
    path.style.strokeDashoffset = `${offset}`;
    
    prevValueRef.current = value;
  }, []); // Only run on mount

  return (
    <div className={cn('gauge-container', 'relative inline-flex flex-col items-center')}>
      <svg
        ref={svgRef}
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="gauge-svg"
        role="img"
        aria-label={`${label}: ${clampedValue} out of ${max}`}
      >
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className="text-border"
          opacity="0.2"
        />
        
        {/* Band segments */}
        <g className="gauge-bands">
          {bandPaths.map((path, i) => (
            <path
              key={i}
              d={path}
              fill="none"
              stroke={bands[i].color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              opacity="0.3"
            />
          ))}
        </g>
        
        {/* Progress arc */}
        <circle
          ref={pathRef}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={animate ? offset : circumference}
          style={{ 
            transition: animate ? 'stroke-dashoffset 600ms ease-out' : 'none',
            transform: 'rotate(-90deg)',
            transformOrigin: 'center',
          }}
          className="gauge-path"
        />
        
        {/* Center value */}
        {showValue && (
          <text
            x={size / 2}
            y={size / 2 + 8}
            textAnchor="middle"
            dominantBaseline="central"
            className="text-data-xl font-bold text-text-primary"
            style={{ pointerEvents: 'none' }}
          >
            {Math.round(clampedValue)}
          </text>
        )}
      </svg>
      
      {label && (
        <div className="mt-3 text-center">
          <p className="text-h3 font-semibold text-text-primary">{label}</p>
        </div>
      )}
    </div>
  );
}

// Simplified Gauge for smaller displays
export function MiniGauge({
  value,
  max = 100,
  size = 80,
  strokeWidth = 8,
  bands = defaultBands,
}: Omit<GaugeProps, 'label' | 'showValue' | 'animate'>) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedValue = Math.max(0, Math.min(max, value));
  const progress = clampedValue / max;
  const offset = circumference * (1 - progress);

  const bandPaths = useMemo(() => {
    return bands.map((band) => {
      const startAngle = (band.min / max) * 360 - 90;
      const endAngle = (band.max / max) * 360 - 90;
      const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0;
      
      const startRad = (startAngle * Math.PI) / 180;
      const endRad = (endAngle * Math.PI) / 180;
      
      const x1 = size / 2 + radius * Math.cos(startRad);
      const y1 = size / 2 + radius * Math.sin(startRad);
      const x2 = size / 2 + radius * Math.cos(endRad);
      const y2 = size / 2 + radius * Math.sin(endRad);
      
      return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`;
    });
  }, [bands, max, radius, size]);

  // Determine color based on value
  const currentBand = bands.find(b => clampedValue >= b.min && clampedValue <= b.max) || bands[0];

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`Value: ${Math.round(clampedValue)}`}>
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className="text-border"
          opacity="0.15"
        />
        
        {/* Band segments (subtle) */}
        <g>
          {bandPaths.map((path, i) => (
            <path
              key={i}
              d={path}
              fill="none"
              stroke={bands[i].color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              opacity="0.2"
            />
          ))}
        </g>
        
        {/* Progress arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={currentBand.color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ 
            transform: 'rotate(-90deg)',
            transformOrigin: 'center',
            transition: 'stroke-dashoffset 600ms ease-out',
          }}
        />
        
        {/* Center value */}
        <text
          x={size / 2}
          y={size / 2 + 4}
          textAnchor="middle"
          dominantBaseline="central"
          className="text-data font-bold"
          fill={currentBand.color}
          style={{ pointerEvents: 'none' }}
        >
          {Math.round(clampedValue)}
        </text>
      </svg>
    </div>
  );
}