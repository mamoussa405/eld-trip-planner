import { useEffect, useMemo } from 'react'
import {
  MapContainer,
  TileLayer,
  Polyline,
  Marker,
  Popup,
  ZoomControl,
  useMap,
} from 'react-leaflet'
import polyline from '@mapbox/polyline'
import type { RouteData, Stop } from '../types'
import { defaultIcon, fuelStopIcon } from './icons/map-icons'

// Default to USA
const MAP_DEFAULT_CENTER = [44.9672, -103.7716]

export default function MapView({ routeData }: { routeData: RouteData | null }) {
  const positions = useMemo(() => {
    if (routeData?.route?.geometry) {
      try {
        return polyline
          .decode(routeData.route.geometry)
          .map((p: number[]) => [p[0], p[1]] as [number, number])
      } catch {
        return null
      }
    }
    return null
  }, [routeData])

  const stops: Stop[] = routeData?.stops ?? []

  return (
    <MapContainer
      center={MAP_DEFAULT_CENTER as [number, number]}
      zoom={6}
      style={{ height: '100%', width: '100%' }}
      zoomControl={false} // Explicitly disable the default control
    >
      <MapCenterAdapter positions={positions} />
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ZoomControl position="topright" />
      {positions && <Polyline positions={positions} weight={5} />}
      {stops.map((s, i) =>
        s.coords ? (
          <Marker
            key={i}
            position={[s.coords[0], s.coords[1]]}
            icon={s.type === 'fuel' ? fuelStopIcon : defaultIcon}
          >
            <Popup>{s.label}</Popup>
          </Marker>
        ) : null
      )}
    </MapContainer>
  )
}

function MapCenterAdapter({ positions }: { positions: [number, number][] | null }) {
  const map = useMap()

  useEffect(() => {
    if (positions) {
      const center = positions[Math.floor(positions.length / 2)]

      map.panTo(center as [number, number])
    }
  }, [positions])

  return null
}
