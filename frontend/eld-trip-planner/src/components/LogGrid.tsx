interface DutyStatus {
  status: 'Off Duty' | 'Sleeper Berth' | 'Driving' | 'On Duty'
  start: number
  end: number
}

interface LogGridProps {
  timeline: DutyStatus[]
}

const statusConfig = {
  'Off Duty': { row: 1, color: '#4CAF50' },
  'Sleeper Berth': { row: 2, color: '#FFC107' },
  'Driving': { row: 3, color: '#F44336' },
  'On Duty': { row: 4, color: '#2196F3' },
}

export default function LogGrid({ timeline }: LogGridProps) {
  const hours = Array.from({ length: 24 }, (_, i) => i)
  const width = 960 // 24 hours * 40px/hr
  const height = 160 // 4 rows * 40px/row
  const rowHeight = 40

  const getStatusY = (status: keyof typeof statusConfig) => {
    // Default to 'Off Duty' if status is not found, though this shouldn't happen
    const config = statusConfig[status] || statusConfig['Off Duty']
    return (config.row - 0.5) * rowHeight
  }

  return (
    <div className="relative" style={{ fontFamily: 'monospace' }}>
      <svg width={width} height={height} className="bg-gray-50">
        {/* Vertical lines and hour markers */}
        {hours.map((hour) => (
          <g key={`hour-line-${hour}`}>
            <line
              x1={hour * 40}
              y1={0}
              x2={hour * 40}
              y2={height}
              stroke={hour % 3 === 0 ? '#999' : '#ddd'}
              strokeWidth="1"
            />
            {[1, 2, 3].map((q) => (
              <line
                key={`q-line-${hour}-${q}`}
                x1={hour * 40 + q * 10}
                y1={0}
                x2={hour * 40 + q * 10}
                y2={height}
                stroke="#eee"
                strokeWidth="1"
              />
            ))}
          </g>
        ))}

        {/* Horizontal lines */}
        {Object.keys(statusConfig).map((_, index) => (
          <line
            key={`status-line-${index}`}
            x1={0}
            y1={(index + 1) * rowHeight}
            x2={width}
            y2={(index + 1) * rowHeight}
            stroke="#ccc"
            strokeWidth="1"
          />
        ))}

        {/* Duty status path */}
        <polyline
          points={timeline
            .map((item) => {
              const startX = item.start * 40
              const endX = item.end * 40
              const y = getStatusY(item.status)
              return `${startX},${y} ${endX},${y}`
            })
            .join(' ')}
          fill="none"
          stroke="black"
          strokeWidth="2"
        />
      </svg>
    </div>
  )
}
