import { AbstractSlider, AbstractRangeSliderView, SliderSpec } from "./abstract_slider";
import { TickFormatter } from "../formatters/tick_formatter";
import * as p from "../../core/properties";
export declare class DateRangeSliderView extends AbstractRangeSliderView {
    model: DateRangeSlider;
    protected _calc_to(): SliderSpec;
}
export declare namespace DateRangeSlider {
    type Attrs = p.AttrsOf<Props>;
    type Props = AbstractSlider.Props;
}
export interface DateRangeSlider extends DateRangeSlider.Attrs {
}
export declare class DateRangeSlider extends AbstractSlider {
    properties: DateRangeSlider.Props;
    __view_type__: DateRangeSliderView;
    constructor(attrs?: Partial<DateRangeSlider.Attrs>);
    behaviour: "drag";
    connected: boolean[];
    protected _formatter(value: number, format: string | TickFormatter): string;
}
//# sourceMappingURL=date_range_slider.d.ts.map