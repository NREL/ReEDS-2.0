import { PlotActionTool, PlotActionToolView } from "./plot_action_tool";
import { Dimensions } from "../../../core/enums";
import * as p from "../../../core/properties";
export declare abstract class ZoomBaseToolView extends PlotActionToolView {
    model: ZoomBaseTool;
    doit(): void;
}
export declare namespace ZoomBaseTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = PlotActionTool.Props & {
        factor: p.Property<number>;
        dimensions: p.Property<Dimensions>;
    };
}
export interface ZoomBaseTool extends ZoomBaseTool.Attrs {
}
export declare abstract class ZoomBaseTool extends PlotActionTool {
    properties: ZoomBaseTool.Props;
    __view_type__: ZoomBaseToolView;
    constructor(attrs?: Partial<ZoomBaseTool.Attrs>);
    get tooltip(): string;
    abstract readonly maintain_focus: boolean;
    abstract get_factor(): number;
}
//# sourceMappingURL=zoom_base_tool.d.ts.map