import React, { useState } from 'react'
import MapView from './components/MapView'
import { getRouteAndLogs } from './api'
import type { RouteData } from './types'
import LogSheet from './components/LogSheet'
import TruckIcon from './components/icons/TruckIcon'
import CrossIcon from './components/icons/CrossIcon'

export default function App() {
  const [loading, setLoading] = useState(false)
  const [routeData, setRouteData] = useState<RouteData | null>(null)
  const [showLogs, setShowLogs] = useState(false)
  const [dailyLogIndex, setDailyLogIndex] = useState(0)
  const [inputs, setInputs] = useState({
    current_location: 'Tangier, Morocco',
    pickup_location: 'Rabat, Morocco',
    dropoff_location: 'Dakhla, Morocco',
    current_cycle_hours: 0,
  })

  const inputFields = [
    {
      name: 'current_location',
      label: 'Current location',
      type: 'text',
    },
    {
      name: 'pickup_location',
      label: 'Pickup location',
      type: 'text',
    },
    {
      name: 'dropoff_location',
      label: 'Dropoff location',
      type: 'text',
    },
    {
      name: 'current_cycle_hours',
      label: 'Current cycle used (hrs)',
      type: 'number',
      step: '1',
    },
  ]

  const handleNextDayClick = () => {
    setDailyLogIndex(dailyLogIndex + 1)
  }

  const handlePrevDayClick = () => {
    setDailyLogIndex(dailyLogIndex - 1)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>, type: string) => {
    const { name, value } = e.target
    setInputs((prev) => ({
      ...prev,
      [name]: type === 'number' ? Number(value) : value,
    }))
  }

  const onSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault()
    setLoading(true)
    try {
      const data = await getRouteAndLogs(inputs)
      setRouteData(data)
    } catch (err: any) {
      alert(err?.response?.data?.detail || err?.message || 'Error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative h-screen w-screen">
      <div className="absolute inset-0 z-0">
        <MapView routeData={routeData} />
      </div>

      <div className="absolute top-3 left-3 z-10 w-96">
        <div className="bg-white rounded-2xl p-6 shadow">
          <h1 className="text-2xl font-semibold mb-6">🚚 Truck Trip Planner & ELD</h1>
          <form onSubmit={onSubmit} className="space-y-3">
            {inputFields.map(({ name, label, type, step }) => (
              <label key={name} className="block">
                <span className="text-sm">{label}</span>
                <input
                  name={name}
                  type={type}
                  step={step}
                  className="mt-1 block w-full rounded-md border p-2 focus-visible:outline-[#ED9B40]"
                  value={inputs[name as keyof typeof inputs]}
                  onChange={(e) => handleInputChange(e, type)}
                />
              </label>
            ))}
            <div className="flex justify-end pt-4">
              <div className="flex gap-3">
                <button
                  type="button"
                  className="px-6 py-2 bg-white hover:bg-gray-100 active:bg-gray-200 rounded-xl font-semibold transition-all duration-300 ease-in-out"
                  onClick={() => {
                    setInputs({
                      current_location: 'Tangier, Morocco',
                      pickup_location: 'Rabat, Morocco',
                      dropoff_location: 'Dakhla, Morocco',
                      current_cycle_hours: 0,
                    })
                    setRouteData(null)
                  }}
                >
                  Reset
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-[#ED9B40] text-black rounded-xl font-semibold hover:bg-[#EA8b1f] active:bg-[#CD7613] transition-all duration-300 ease-in-out"
                  disabled={loading}
                >
                  {loading ? 'Planning...' : 'Plan Trip'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
      <div
        className={`flex justify-end w-full absolute bottom-6 right-2 ${routeData?.logs.length ? '' : 'pointer-events-none'}`}
      >
        <button
          type="button"
          className={`w-[50px] h-[50px] bg-[#33658A] hover:w-[135px] hover:bg-[#2c5777] active:bg-[#214159] rounded-full font-semibold transition-all duration-300 ease-in-out overflow-hidden shadow-[0px_1px_5px_0px_#00000042] ${routeData?.logs.length ? 'opacity-100' : 'opacity-0'}`}
          disabled={routeData && routeData?.logs?.length <= 0 ? true : false}
          onClick={() => {
            setShowLogs(true)
          }}
        >
          <div className="relative px-6">
            <div className="absolute top-[-12px] left-3">
              <TruckIcon color="#ffffff" />
            </div>
            <span className="absolute top-[-10px] left-[50px] whitespace-nowrap text-white">
              ELD Logs
            </span>
          </div>
        </button>
      </div>
      {showLogs && routeData?.logs.length && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center">
          <div className="bg-gray-100 rounded-2xl shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden">
            <div className="sticky top-0 bg-white p-4 pl-8 flex justify-between items-center">
              <h2 className="text-2xl font-bold">Driver's Daily Logs</h2>
              <button
                onClick={() => setShowLogs(false)}
                className="text-gray-500 hover:text-gray-800 hover:cursor-pointer text-3xl font-bold"
              >
                <CrossIcon />
              </button>
            </div>
            <div className="p-4 bg-white">
              <LogSheet
                dayIndex={dailyLogIndex}
                numberOfDays={routeData?.logs.length}
                logData={routeData.logs[dailyLogIndex]}
                onNextDayClick={handleNextDayClick}
                onPrevDayClick={handlePrevDayClick}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
