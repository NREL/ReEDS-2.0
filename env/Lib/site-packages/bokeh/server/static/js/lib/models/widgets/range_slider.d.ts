import { AbstractSlider, AbstractRangeSliderView } from "./abstract_slider";
import { TickFormatter } from "../formatters/tick_formatter";
import * as p from "../../core/properties";
export declare class RangeSliderView extends AbstractRangeSliderView {
    model: RangeSlider;
}
export declare namespace RangeSlider {
    type Attrs = p.AttrsOf<Props>;
    type Props = AbstractSlider.Props;
}
export interface RangeSlider extends RangeSlider.Attrs {
}
export declare class RangeSlider extends AbstractSlider {
    properties: RangeSlider.Props;
    __view_type__: RangeSliderView;
    constructor(attrs?: Partial<RangeSlider.Attrs>);
    behaviour: "drag";
    connected: boolean[];
    protected _formatter(value: number, format: string | TickFormatter): string;
}
//# sourceMappingURL=range_slider.d.ts.map