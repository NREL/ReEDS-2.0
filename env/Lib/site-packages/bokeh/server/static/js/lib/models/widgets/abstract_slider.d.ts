import { API } from "nouislider";
import * as p from "../../core/properties";
import { Color } from "../../core/types";
import { StyleSheetLike } from "../../core/dom";
import { OrientedControl, OrientedControlView } from "./oriented_control";
import { TickFormatter } from "../formatters/tick_formatter";
export interface SliderSpec {
    start: number;
    end: number;
    value: number[];
    step: number;
}
declare abstract class AbstractBaseSliderView extends OrientedControlView {
    model: AbstractSlider;
    protected group_el: HTMLElement;
    protected slider_el?: HTMLElement;
    protected title_el: HTMLElement;
    protected readonly _auto_width = "auto";
    protected readonly _auto_height = "auto";
    controls(): Generator<HTMLInputElement, void, unknown>;
    private _noUiSlider;
    get _steps(): API["steps"];
    connect_signals(): void;
    stylesheets(): StyleSheetLike[];
    _update_title(): void;
    protected _set_bar_color(): void;
    protected abstract _calc_to(): SliderSpec;
    protected abstract _calc_from(values: number[]): number | number[];
    render(): void;
    protected _slide(values: number[]): void;
    protected _change(values: number[]): void;
}
export declare abstract class AbstractSliderView extends AbstractBaseSliderView {
    protected _calc_to(): SliderSpec;
    protected _calc_from([value]: number[]): number;
}
export declare abstract class AbstractRangeSliderView extends AbstractBaseSliderView {
    protected _calc_to(): SliderSpec;
    protected _calc_from(values: number[]): number[];
}
export declare namespace AbstractSlider {
    type Attrs = p.AttrsOf<Props>;
    type Props = OrientedControl.Props & {
        title: p.Property<string | null>;
        show_value: p.Property<boolean>;
        start: p.Property<any>;
        end: p.Property<any>;
        value: p.Property<any>;
        value_throttled: p.Property<any>;
        step: p.Property<number>;
        format: p.Property<string | TickFormatter>;
        direction: p.Property<"ltr" | "rtl">;
        tooltips: p.Property<boolean>;
        bar_color: p.Property<Color>;
    };
}
export interface AbstractSlider extends AbstractSlider.Attrs {
}
export declare abstract class AbstractSlider extends OrientedControl {
    properties: AbstractSlider.Props;
    constructor(attrs?: Partial<AbstractSlider.Attrs>);
    behaviour: "drag" | "tap";
    connected: false | boolean[];
    protected abstract _formatter(value: number, format: string | TickFormatter): string;
    pretty(value: number): string;
}
export {};
//# sourceMappingURL=abstract_slider.d.ts.map