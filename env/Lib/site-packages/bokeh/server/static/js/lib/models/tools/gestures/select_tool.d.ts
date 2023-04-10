import { GestureTool, GestureToolView } from "./gesture_tool";
import { DataRenderer } from "../../renderers/data_renderer";
import { DataSource } from "../../sources/data_source";
import * as p from "../../../core/properties";
import { KeyEvent, KeyModifiers } from "../../../core/ui_events";
import { SelectionMode } from "../../../core/enums";
import { Geometry } from "../../../core/geometry";
import { Signal0 } from "../../../core/signaling";
import { MenuItem } from "../../../core/util/menus";
export declare abstract class SelectToolView extends GestureToolView {
    model: SelectTool;
    connect_signals(): void;
    get computed_renderers(): DataRenderer[];
    _computed_renderers_by_data_source(): Map<DataSource, DataRenderer[]>;
    protected _clear_overlay(): void;
    protected _clear_other_overlays(): void;
    protected _clear_selection(): void;
    protected _select_mode(ev: KeyModifiers): SelectionMode;
    _keyup(ev: KeyEvent): void;
    _clear(): void;
    abstract _select(geometry: Geometry, final: boolean, mode: SelectionMode): void;
    protected _emit_selection_event(geometry: Geometry, final?: boolean): void;
}
export declare namespace SelectTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = GestureTool.Props & {
        renderers: p.Property<DataRenderer[] | "auto">;
        mode: p.Property<SelectionMode>;
    };
}
export interface SelectTool extends SelectTool.Attrs {
}
export declare abstract class SelectTool extends GestureTool {
    properties: SelectTool.Props;
    __view_type__: SelectToolView;
    clear: Signal0<this>;
    constructor(attrs?: Partial<SelectTool.Attrs>);
    initialize(): void;
    get menu(): MenuItem[] | null;
}
//# sourceMappingURL=select_tool.d.ts.map