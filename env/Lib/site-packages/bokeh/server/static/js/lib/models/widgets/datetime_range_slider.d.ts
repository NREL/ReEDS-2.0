import { AbstractSlider, AbstractRangeSliderView } from "./abstract_slider";
import { TickFormatter } from "../formatters/tick_formatter";
import * as p from "../../core/properties";
export declare class DatetimeRangeSliderView extends AbstractRangeSliderView {
    model: DatetimeRangeSlider;
}
export declare namespace DatetimeRangeSlider {
    type Attrs = p.AttrsOf<Props>;
    type Props = AbstractSlider.Props;
}
export interface DatetimeRangeSlider extends DatetimeRangeSlider.Attrs {
}
export declare class DatetimeRangeSlider extends AbstractSlider {
    properties: DatetimeRangeSlider.Props;
    __view_type__: DatetimeRangeSliderView;
    constructor(attrs?: Partial<DatetimeRangeSlider.Attrs>);
    behaviour: "drag";
    connected: boolean[];
    protected _formatter(value: number, format: string | TickFormatter): string;
}
//# sourceMappingURL=datetime_range_slider.d.ts.map