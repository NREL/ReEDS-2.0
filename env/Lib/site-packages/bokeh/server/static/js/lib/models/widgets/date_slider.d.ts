import { AbstractSlider, AbstractSliderView, SliderSpec } from "./abstract_slider";
import { TickFormatter } from "../formatters/tick_formatter";
import * as p from "../../core/properties";
export declare class DateSliderView extends AbstractSliderView {
    model: DateSlider;
    protected _calc_to(): SliderSpec;
}
export declare namespace DateSlider {
    type Attrs = p.AttrsOf<Props>;
    type Props = AbstractSlider.Props;
}
export interface DateSlider extends DateSlider.Attrs {
}
export declare class DateSlider extends AbstractSlider {
    properties: DateSlider.Props;
    __view_type__: DateSliderView;
    constructor(attrs?: Partial<DateSlider.Attrs>);
    behaviour: "tap";
    connected: boolean[];
    protected _formatter(value: number, format: string | TickFormatter): string;
}
//# sourceMappingURL=date_slider.d.ts.map