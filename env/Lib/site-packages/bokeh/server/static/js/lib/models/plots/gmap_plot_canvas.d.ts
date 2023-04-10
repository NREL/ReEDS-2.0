import { GMapPlot } from "./gmap_plot";
import { PlotView } from "./plot_canvas";
import { RangeInfo, RangeOptions } from "./range_manager";
type GMapRangeInfo = RangeInfo & {
    sdx?: number;
    sdy?: number;
    factor?: number;
};
declare global {
    interface Window {
        _bokeh_gmaps_callback: () => void;
    }
}
export declare class GMapPlotView extends PlotView {
    model: GMapPlot;
    protected _tiles_loaded: boolean;
    protected zoom_count: number;
    protected initial_zoom: number;
    protected initial_lat: number;
    protected initial_lng: number;
    protected map_el: HTMLElement;
    private map;
    protected map_types: any;
    protected _api_key: string;
    initialize(): void;
    lazy_initialize(): Promise<void>;
    remove(): void;
    update_range(range_info: GMapRangeInfo | null, options?: RangeOptions): void;
    protected _build_map(): void;
    protected _render_finished(): void;
    has_finished(): boolean;
    protected _get_latlon_bounds(): [number, number, number, number];
    protected _get_projected_bounds(): [number, number, number, number];
    protected _set_bokeh_ranges(): void;
    protected _update_center(fld: "lat" | "lng"): void;
    protected _update_map_type(): void;
    protected _update_scale_control(): void;
    protected _update_tilt(): void;
    protected _update_options(): void;
    protected _update_styling(): void;
    protected _update_zoom(): void;
    _after_layout(): void;
}
export {};
//# sourceMappingURL=gmap_plot_canvas.d.ts.map