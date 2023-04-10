import { Signal } from "./signaling";
import { Keys } from "./dom";
import { PlotView } from "../models/plots/plot";
import { ToolView } from "../models/tools/tool";
import { RendererView } from "../models/renderers/renderer";
import type { CanvasView } from "../models/canvas/canvas";
export interface Moveable {
    _move_start(ev: MoveEvent): boolean;
    _move(ev: MoveEvent): void;
    _move_end(ev: MoveEvent): void;
}
export interface Pannable {
    _pan_start(ev: PanEvent): boolean;
    _pan(ev: PanEvent): void;
    _pan_end(ev: PanEvent): void;
}
export interface Pinchable {
    _pinch_start(ev: PinchEvent): boolean;
    _pinch(ev: PinchEvent): void;
    _pinch_end(ev: PinchEvent): void;
}
export interface Rotatable {
    _rotate_start(ev: RotateEvent): boolean;
    _rotate(ev: RotateEvent): void;
    _rotate_end(ev: RotateEvent): void;
}
export interface Scrollable {
    _scroll(ev: ScrollEvent): void;
}
export interface Keyable {
    _keydown(ev: KeyEvent): void;
    _keyup(ev: KeyEvent): void;
}
export interface Tapable {
    _tap(ev: TapEvent): void;
    _doubletap?(ev: TapEvent): void;
    _press?(ev: TapEvent): void;
    _pressup?(ev: TapEvent): void;
}
export declare function is_Moveable(obj: unknown): obj is Moveable;
export declare function is_Pannable(obj: unknown): obj is Pannable;
export declare function is_Pinchable(obj: unknown): obj is Pinchable;
export declare function is_Rotatable(obj: unknown): obj is Rotatable;
export declare function is_Scrollable(obj: unknown): obj is Scrollable;
export declare function is_Keyable(obj: unknown): obj is Keyable;
export declare function is_Tapable(obj: unknown): obj is Keyable;
type HammerEvent = {
    type: string;
    deltaX: number;
    deltaY: number;
    scale: number;
    rotation: number;
    srcEvent: TouchEvent | MouseEvent | PointerEvent;
};
export type ScreenCoord = {
    sx: number;
    sy: number;
};
export type KeyModifiers = {
    shift_key: boolean;
    ctrl_key: boolean;
    alt_key: boolean;
};
export type PanEvent = {
    type: "pan" | "panstart" | "panend";
    sx: number;
    sy: number;
    dx: number;
    dy: number;
} & KeyModifiers;
export type PinchEvent = {
    type: "pinch" | "pinchstart" | "pinchend";
    sx: number;
    sy: number;
    scale: number;
} & KeyModifiers;
export type RotateEvent = {
    type: "rotate" | "rotatestart" | "rotateend";
    sx: number;
    sy: number;
    rotation: number;
} & KeyModifiers;
export type GestureEvent = PanEvent | PinchEvent | RotateEvent;
export type TapEvent = {
    type: "tap" | "doubletap" | "press" | "pressup" | "contextmenu";
    sx: number;
    sy: number;
} & KeyModifiers;
export type MoveEvent = {
    type: "mousemove" | "mouseenter" | "mouseleave";
    sx: number;
    sy: number;
} & KeyModifiers;
export type ScrollEvent = {
    type: "wheel";
    sx: number;
    sy: number;
    delta: number;
} & KeyModifiers;
export type UIEvent = GestureEvent | TapEvent | MoveEvent | ScrollEvent;
export type KeyEvent = {
    type: "keyup" | "keydown";
    key: Keys;
} & KeyModifiers;
export type EventType = "pan" | "pinch" | "rotate" | "move" | "tap" | "doubletap" | "press" | "pressup" | "scroll";
export type UISignal<E> = Signal<{
    id: string | null;
    e: E;
}, UIEventBus>;
export declare class UIEventBus implements EventListenerObject {
    readonly canvas_view: CanvasView;
    readonly pan_start: UISignal<PanEvent>;
    readonly pan: UISignal<PanEvent>;
    readonly pan_end: UISignal<PanEvent>;
    readonly pinch_start: UISignal<PinchEvent>;
    readonly pinch: UISignal<PinchEvent>;
    readonly pinch_end: UISignal<PinchEvent>;
    readonly rotate_start: UISignal<RotateEvent>;
    readonly rotate: UISignal<RotateEvent>;
    readonly rotate_end: UISignal<RotateEvent>;
    readonly tap: UISignal<TapEvent>;
    readonly doubletap: UISignal<TapEvent>;
    readonly press: UISignal<TapEvent>;
    readonly pressup: UISignal<TapEvent>;
    readonly move_enter: UISignal<MoveEvent>;
    readonly move: UISignal<MoveEvent>;
    readonly move_exit: UISignal<MoveEvent>;
    readonly scroll: UISignal<ScrollEvent>;
    readonly keydown: UISignal<KeyEvent>;
    readonly keyup: UISignal<KeyEvent>;
    private readonly hammer;
    get hit_area(): HTMLElement;
    constructor(canvas_view: CanvasView);
    destroy(): void;
    handleEvent(e: KeyboardEvent): void;
    protected _configure_hammerjs(): void;
    register_tool(tool_view: ToolView): void;
    private _register_tool;
    protected _hit_test_renderers(plot_view: PlotView, sx: number, sy: number): RendererView | null;
    set_cursor(cursor?: string): void;
    protected _hit_test_frame(plot_view: PlotView, sx: number, sy: number): boolean;
    protected _hit_test_plot(sx: number, sy: number): PlotView | null;
    protected _prev_move: {
        sx: number;
        sy: number;
        plot_view: PlotView | null;
    } | null;
    protected _curr_pan: {
        plot_view: PlotView;
    } | null;
    protected _curr_pinch: {
        plot_view: PlotView;
    } | null;
    protected _curr_rotate: {
        plot_view: PlotView;
    } | null;
    _trigger<E extends UIEvent>(signal: UISignal<E>, e: E, srcEvent: Event): void;
    private _current_pan_view;
    private _current_pinch_view;
    private _current_rotate_view;
    private _current_move_view;
    __trigger<E extends UIEvent>(plot_view: PlotView, signal: UISignal<E>, e: E, srcEvent: Event): void;
    trigger<E>(signal: UISignal<E>, e: E, id?: string | null): void;
    _trigger_bokeh_event(plot_view: PlotView, e: UIEvent): void;
    _get_sxy(event: TouchEvent | MouseEvent | PointerEvent): ScreenCoord;
    _pan_event(e: HammerEvent): PanEvent;
    _pinch_event(e: HammerEvent): PinchEvent;
    _rotate_event(e: HammerEvent): RotateEvent;
    _tap_event(e: HammerEvent): TapEvent;
    _move_event(e: MouseEvent): MoveEvent;
    _scroll_event(e: WheelEvent): ScrollEvent;
    _key_event(e: KeyboardEvent): KeyEvent;
    _pan_start(e: HammerEvent): void;
    _pan(e: HammerEvent): void;
    _pan_end(e: HammerEvent): void;
    _pinch_start(e: HammerEvent): void;
    _pinch(e: HammerEvent): void;
    _pinch_end(e: HammerEvent): void;
    _rotate_start(e: HammerEvent): void;
    _rotate(e: HammerEvent): void;
    _rotate_end(e: HammerEvent): void;
    _tap(e: HammerEvent): void;
    _doubletap(e: HammerEvent): void;
    _press(e: HammerEvent): void;
    _pressup(e: HammerEvent): void;
    _mouse_enter(e: MouseEvent): void;
    _mouse_move(e: MouseEvent): void;
    _mouse_exit(e: MouseEvent): void;
    _mouse_wheel(e: WheelEvent): void;
    _context_menu(_e: MouseEvent): void;
    _key_down(e: KeyboardEvent): void;
    _key_up(e: KeyboardEvent): void;
}
export {};
//# sourceMappingURL=ui_events.d.ts.map