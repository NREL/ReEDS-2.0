import { Axis, AxisView, Extents, TickCoords, Coords } from "./axis";
import { CategoricalTicker } from "../tickers/categorical_ticker";
import { CategoricalTickFormatter } from "../formatters/categorical_tick_formatter";
import * as visuals from "../../core/visuals";
import * as mixins from "../../core/property_mixins";
import * as p from "../../core/properties";
import { TickLabelOrientation } from "../../core/enums";
import { GraphicsBoxes } from "../../core/graphics";
import { Context2d } from "../../core/util/canvas";
import { Orient } from "../../core/layout/side_panel";
export type CategoricalTickCoords = TickCoords & {
    mids: Coords;
    tops: Coords;
};
export declare class CategoricalAxisView extends AxisView {
    model: CategoricalAxis;
    visuals: CategoricalAxis.Visuals;
    protected _paint(ctx: Context2d, extents: Extents, tick_coords: TickCoords): void;
    protected _draw_group_separators(ctx: Context2d, _extents: Extents, _tick_coords: TickCoords): void;
    protected _draw_major_labels(ctx: Context2d, extents: Extents, _tick_coords: TickCoords): void;
    protected _tick_label_extents(): number[];
    protected _get_factor_info(): [GraphicsBoxes, Coords, Orient | number, visuals.Text][];
    get tick_coords(): CategoricalTickCoords;
}
export declare namespace CategoricalAxis {
    type Attrs = p.AttrsOf<Props>;
    type Props = Axis.Props & {
        ticker: p.Property<CategoricalTicker>;
        formatter: p.Property<CategoricalTickFormatter>;
        group_label_orientation: p.Property<TickLabelOrientation | number>;
        subgroup_label_orientation: p.Property<TickLabelOrientation | number>;
    } & Mixins;
    type Mixins = mixins.SeparatorLine & mixins.GroupText & mixins.SubGroupText;
    type Visuals = Axis.Visuals & {
        separator_line: visuals.Line;
        group_text: visuals.Text;
        subgroup_text: visuals.Text;
    };
}
export interface CategoricalAxis extends CategoricalAxis.Attrs {
}
export declare class CategoricalAxis extends Axis {
    properties: CategoricalAxis.Props;
    __view_type__: CategoricalAxisView;
    ticker: CategoricalTicker;
    formatter: CategoricalTickFormatter;
    constructor(attrs?: Partial<CategoricalAxis.Attrs>);
}
//# sourceMappingURL=categorical_axis.d.ts.map