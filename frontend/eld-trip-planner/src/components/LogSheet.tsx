import ChevronLeftIcon from './icons/ChevronLeftIcon'
import ChevronRightIcon from './icons/ChevronRightIcon'
import LogGrid from './LogGrid'

interface DutyStatus {
  status: 'Off Duty' | 'Sleeper Berth' | 'Driving' | 'On Duty'
  start: number
  end: number
}

export interface DailyLogData {
  day: number
  off_duty_hours: number
  sleeper_berth_hours: number
  driving_hours: number
  on_duty_hours: number
  total_on_duty: number
  cycle_hours_after: number
  daily_distance_miles: number
  duty_status_timeline: DutyStatus[]
  note?: string
  type?: string
}

interface LogSheetProps {
  logData: DailyLogData
  dayIndex: number
  numberOfDays: number
  onNextDayClick: () => void
  onPrevDayClick: () => void
}

const LOG_SHEET_WIDTH = 960 // 24 hours * 40px/hr

export default function LogSheet({
  logData,
  dayIndex,
  numberOfDays,
  onNextDayClick,
  onPrevDayClick,
}: LogSheetProps) {
  const halfDayTimeline = Array.from({ length: 11 }, (_, i) => i + 1)
  const oneDaytimeline = ['Mid', ...halfDayTimeline, 'Noon', ...halfDayTimeline]
  const dutyStatusRows = [
    { label: '1. Off Duty', hours: logData.off_duty_hours },
    { label: '2. Sleeper Berth', hours: logData.sleeper_berth_hours },
    { label: '3. Driving', hours: logData.driving_hours },
    { label: '4. On Duty (not driving)', hours: logData.on_duty_hours },
  ]

  return (
    <div className="px-6 mb-5">
      <div className="flex justify-center items-center">
        <div className="flex justify-between items-center gap-2">
          <button
            className="px-6 py-2 bg-white hover:bg-gray-100 rounded-full active:bg-gray-200 font-semibold transition-all duration-300 ease-in-out"
            style={{ opacity: dayIndex <= 0 ? 0 : 100 }}
            disabled={dayIndex <= 0}
            onClick={onPrevDayClick}
          >
            <ChevronLeftIcon />
          </button>
          <strong className="text-lg whitespace-nowrap">Day {dayIndex + 1}</strong>
          <button
            className="px-6 py-2 bg-white hover:bg-gray-100 rounded-full active:bg-gray-200 font-semibold transition-all duration-300 ease-in-out"
            style={{ opacity: dayIndex >= numberOfDays - 1 ? 0 : 100 }}
            disabled={dayIndex >= numberOfDays - 1}
            onClick={onNextDayClick}
          >
            <ChevronRightIcon />
          </button>
        </div>
      </div>

      <div className="flex flex-col mt-4">
        <div className="flex">
          <div className="flex justify-end w-full">
            <div className="flex" style={{ width: `${LOG_SHEET_WIDTH}px` }}>
              {oneDaytimeline.map((label, i) => (
                <div key={i} className="flex items-end text-xs" style={{ width: '40px' }}>
                  {label}
                </div>
              ))}
            </div>
          </div>
          <div className="flex items-end text-xs" style={{ width: '40px' }}>
            Mid
          </div>
          <div className="font-bold text-end w-[60px]">Total Hours</div>
        </div>
        <div className="flex">
          <div className="flex flex-col text-sm">
            {dutyStatusRows.map((row) => (
              <div key={row.label} className="h-10 flex items-center border-b">
                {row.label}
              </div>
            ))}
          </div>
          <div className="flex-grow">
            <LogGrid timeline={logData.duty_status_timeline} />
          </div>
          <div className="pl-4">
            {dutyStatusRows.map((row) => (
              <div key={row.label} className="h-10 flex justify-end items-center border-b">
                {row.hours}
              </div>
            ))}
            <div className="h-10 flex justify-end items-center border-b font-bold">
              {dutyStatusRows.reduce((sum, r) => sum + r.hours, 0)}
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center" style={{ width: `${LOG_SHEET_WIDTH}px` }}>
        <div>
          <p>
            <strong>Total Miles Driving Today:</strong> {logData.daily_distance_miles}
          </p>
        </div>
        <div className="flex justify-center items-center w-[50px] h-[50px] border-[2px] border-red-600 rounded-full">
          <strong>{logData.total_on_duty}</strong>
        </div>
      </div>
    </div>
  )
}
