export interface Stop {
  type: string;
  coords?: [number, number];
  progress?: number;
  label: string;
}

export interface RouteData {
  route: {
    distance_m: number;
    duration_s: number;
    geometry?: string;
    legs?: any[];
  };
  stops: Stop[];
  logs: any[];
}
