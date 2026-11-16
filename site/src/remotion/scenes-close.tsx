import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import items from '../items.json';
import {Browser, C, Card, MONO, Robot, Scene, Stamp, Step, Wordmark, fade, useAsset, useIn} from './theme';
import {pickXY} from './scenes-open';

const money = (n: number) => '$' + n.toLocaleString('en-US', {minimumFractionDigits: n % 1 ? 2 : 0, maximumFractionDigits: 2});
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// What buyers paid (price + shipping) on eBay sold listings for this exact kit, Nov 2026.
const PAID = [380, 321, 375, 383.55, 321.67, 479.98, 425.12, 309.22, 367.62];
const pct = (xs: number[], p: number) => {
  const s = [...xs].sort((a, b) => a - b), i = (s.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i);
  return s[lo] + (s[hi] - s[lo]) * (i - lo);
};

export const Price: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const asset = useAsset();
  const move = spring({frame: f, fps, config: {damping: 22}});
  const start = pickXY(0, 0);
  const scroll = interpolate(f, [12, 120], [0, -1040], {...clamp, easing: (t) => t * t * (3 - 2 * t)});
  const win = fade(f, 0, 10);
  const found = Math.min(PAID.length, Math.max(0, Math.floor((f - 14) / 11)));
  return (
    <Scene>
      <Step n={3} title="Find what it really sells for" who="Claude reads eBay’s sold listings in your browser" />
      <div style={{position: 'absolute', left: 80, top: 180, width: 1110, height: 850, opacity: win, transform: `translateY(${(1 - win) * 30}px)`, borderRadius: 14, overflow: 'hidden', boxShadow: '0 12px 40px rgba(0,0,0,.18)', background: '#fff'}}>
        <div style={{height: 84, display: 'flex', alignItems: 'center', gap: 22, padding: '0 24px', borderBottom: `1px solid ${C.line}`, background: '#fff', position: 'relative', zIndex: 2}}>
          <Wordmark site="ebay" size={52} />
          <div style={{flex: 1, border: '2px solid #191919', borderRadius: 26, padding: '10px 20px', fontSize: 24}}>dji mavic air 2 fly more combo</div>
          <div style={{background: '#3665f3', color: '#fff', fontWeight: 700, fontSize: 22, borderRadius: 26, padding: '12px 30px'}}>Search</div>
        </div>
        <Img src={asset('img/ebay-sold.jpg')} style={{width: 1110, position: 'absolute', top: 84 + scroll}} />
        <div style={{position: 'absolute', right: 18, bottom: 18, zIndex: 2, background: 'rgba(28,30,33,.88)', color: '#fff', borderRadius: 12, padding: '10px 18px', fontSize: 22, fontWeight: 700}}>
          Playwright · signed-in browser
        </div>
      </div>
      <div style={{position: 'absolute', left: 1240, top: 180, right: 80, display: 'flex', flexDirection: 'column', gap: 18, opacity: win}}>
        <div style={{height: 300}} />
        <Card style={{padding: '16px 22px'}}>
          <div style={{fontSize: 20, fontWeight: 800, color: C.muted}}>SAME KIT, SOLD THIS MONTH</div>
          <div style={{fontSize: 46, fontWeight: 800}}>{found} sales</div>
          <div style={{fontSize: 20, color: C.muted, opacity: fade(f, 118, 128)}}>Dropped: parts-only and drone-only listings</div>
        </Card>
        <div style={{display: 'flex', gap: 14, opacity: fade(f, 120, 135)}}>
          <Chip k="Floor (25th pct)" v={money(Math.round(pct(PAID, 0.25)))} />
          <Chip k="Median" v={money(Math.round(pct(PAID, 0.5)))} />
        </div>
        <Card style={{padding: '14px 22px', opacity: fade(f, 140, 155)}}>
          <Row k="Facebook" v="$390" note="local cash, no fees" />
          <Row k="eBay" v="$425" note="buyer pays shipping" />
        </Card>
      </div>
      <Img src={asset('img/roll/R116-1.jpg')} style={{position: 'absolute', borderRadius: 14, objectFit: 'cover', boxShadow: '0 4px 14px rgba(0,0,0,.25)',
        left: interpolate(move, [0, 1], [start.x, 1240]), top: interpolate(move, [0, 1], [start.y, 180]),
        width: interpolate(move, [0, 1], [150, 600]), height: interpolate(move, [0, 1], [150, 300]), transform: `rotate(${-4 * (1 - move)}deg)`}} />
      <div style={{position: 'absolute', left: 1256, top: 440, color: '#fff', fontSize: 26, fontWeight: 800, textShadow: '0 1px 8px rgba(0,0,0,.8)', opacity: fade(f, 14, 24)}}>
        DJI Mavic Air 2 Fly More Combo
      </div>
    </Scene>
  );
};

const Chip: React.FC<{k: string; v: string}> = ({k, v}) => (
  <div style={{flex: 1, background: C.waitSoft, color: C.waitInk, borderRadius: 14, padding: '12px 18px'}}>
    <div style={{fontSize: 18, fontWeight: 700}}>{k}</div><div style={{fontSize: 40, fontWeight: 800}}>{v}</div>
  </div>
);
const Row: React.FC<{k: string; v: string; note: string}> = ({k, v, note}) => (
  <div style={{display: 'flex', alignItems: 'baseline', gap: 14, padding: '5px 0'}}>
    <span style={{width: 130, fontSize: 26, fontWeight: 700}}>{k}</span>
    <span style={{fontSize: 34, fontWeight: 800}}>{v}</span>
    <span style={{fontSize: 19, color: C.muted}}>{note}</span>
  </div>
);

const TITLE = 'DJI Mavic Air 2 Fly More Combo, 3 Batteries, ND Filters, Spare Props & Bag';

const Field: React.FC<{k: string; v: string; mono?: boolean}> = ({k, v, mono}) => (
  <div style={{display: 'flex', flexDirection: 'column', gap: 2, border: `1px solid ${C.line}`, borderRadius: 8, padding: '6px 12px'}}>
    <span style={{fontSize: 14, color: C.muted, fontWeight: 600}}>{k}</span>
    <span style={{fontSize: 19, fontWeight: 600, fontFamily: mono ? MONO : undefined, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{v || ' '}</span>
  </div>
);

const SiteWin: React.FC<{site: 'ebay' | 'fb' | 'mercari' | 'swappa'; at: number; x: number; y: number; children: React.ReactNode; head?: string}> = ({site, at, x, y, children, head}) => {
  const p = useIn(at, 16);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: 860, height: 410, borderRadius: 14, overflow: 'hidden', background: '#fff',
      boxShadow: '0 10px 30px rgba(0,0,0,.18)', opacity: p, transform: `translateY(${(1 - p) * 30}px)`}}>
      <div style={{height: 70, display: 'flex', alignItems: 'center', gap: 18, padding: '0 22px', borderBottom: `1px solid ${C.line}`}}>
        <Wordmark site={site} size={40} /><span style={{fontSize: 20, fontWeight: 700, color: C.muted}}>{head}</span>
      </div>
      <div style={{padding: 20, height: 340}}>{children}</div>
    </div>
  );
};

export const Drafts: React.FC = () => {
  const f = useCurrentFrame();
  const asset = useAsset();
  const typed = (at: number) => TITLE.slice(0, Math.max(0, Math.floor((f - at) * 5)));
  const photo = (w: number, h: number) => <Img src={asset('img/hero/dji-2.jpg')} style={{width: w, height: h, objectFit: 'cover', borderRadius: 8}} />;
  return (
    <Scene>
      <Step n={4} title="Draft it everywhere it fits" who="Claude fills each site’s own form, then stops" />
      <SiteWin site="ebay" head="Complete your listing" at={4} x={80} y={180}>
        <div style={{display: 'flex', gap: 18}}>
          {photo(250, 250)}
          <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 10, minWidth: 0}}>
            <Field k={`Title · ${typed(14).length}/80`} v={typed(14)} />
            <div style={{display: 'flex', gap: 10}}><Field k="Condition" v="Used" /><Field k="Format" v="Buy It Now" /><Field k="Price" v="$425.00" /></div>
            <div style={{display: 'flex', justifyContent: 'flex-end', marginTop: 8}}>
              <span style={{background: '#3665f3', color: '#fff', borderRadius: 24, padding: '10px 30px', fontSize: 20, fontWeight: 700}}>List it</span>
            </div>
          </div>
        </div>
      </SiteWin>
      <SiteWin site="fb" head="Item for sale" at={16} x={980} y={180}>
        <div style={{display: 'flex', gap: 18}}>
          <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 10, minWidth: 0}}>
            <Field k="Title" v={typed(26)} />
            <Field k="Price" v="$390" />
            <div style={{display: 'flex', gap: 10}}><Field k="Category" v="Electronics" /><Field k="Condition" v="Used – Good" /></div>
            <span style={{alignSelf: 'flex-start', background: '#0866ff', color: '#fff', borderRadius: 8, padding: '10px 26px', fontSize: 20, fontWeight: 700, marginTop: 4}}>Publish</span>
          </div>
          <div style={{width: 250, background: C.ground, borderRadius: 10, padding: 10}}>
            {photo(230, 170)}
            <div style={{fontSize: 22, fontWeight: 800, marginTop: 6}}>$390</div>
            <div style={{fontSize: 15, lineHeight: 1.25}}>{TITLE.slice(0, 44)}…</div>
          </div>
        </div>
      </SiteWin>
      <SiteWin site="mercari" head="Listing details" at={28} x={80} y={615}>
        <div style={{display: 'flex', gap: 18}}>
          {photo(250, 250)}
          <div style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 10, minWidth: 0}}>
            <Field k="Title" v={typed(38)} />
            <div style={{display: 'flex', gap: 10}}><Field k="Condition" v="Good" /><Field k="Shipping" v="Buyer pays" /><Field k="Price" v="$425" /></div>
            <div style={{display: 'flex', justifyContent: 'flex-end', marginTop: 8}}>
              <span style={{background: '#4f3cf0', color: '#fff', borderRadius: 24, padding: '10px 30px', fontSize: 20, fontWeight: 700}}>List</span>
            </div>
          </div>
        </div>
      </SiteWin>
      <SiteWin site="swappa" head="Sell" at={40} x={980} y={615}>
        <div style={{display: 'flex', gap: 22, alignItems: 'center', height: '100%'}}>
          <div style={{filter: 'grayscale(1)', opacity: 0.5}}>{photo(250, 250)}</div>
          <div style={{fontSize: 28, fontWeight: 700, color: C.muted, lineHeight: 1.35}}>Skipped.<br /><span style={{fontWeight: 500, fontSize: 24}}>Swappa lists by catalog model, and drones aren’t in its catalog.</span></div>
        </div>
      </SiteWin>
    </Scene>
  );
};

// Step 5 turns into step 6: drafts go live, then two weeks later they're sold.
export const PublishSold: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const asset = useAsset();
  const later = fade(f, 78, 92);
  const cx = interpolate(f, [8, 34], [1500, 1080], clamp), cy = interpolate(f, [8, 34], [1060, 952], clamp);
  const clicked = f >= 38;
  return (
    <Scene>
      <div style={{opacity: 1 - later}}><Step n={5} title="You press Publish" who="One review, one click. Only you post." human /></div>
      <div style={{opacity: later, position: 'absolute', inset: 0}}>{f >= 78 && <Step n={6} title="Two weeks later" who="Most of it sold" human />}</div>
      <div style={{position: 'absolute', left: 80, right: 80, top: 190, display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 20}}>
        {items.map((it, i) => {
          const live = spring({frame: f - 40 - i * 1.5, fps, config: {damping: 14}});
          const sold = spring({frame: f - 92 - i * 3, fps, config: {damping: 12}});
          return (
            <div key={it.uid} style={{position: 'relative'}}>
              <Img src={asset(it.photos[0])} style={{width: '100%', aspectRatio: '1', objectFit: 'cover', borderRadius: 12}} />
              <span style={{position: 'absolute', right: 10, top: 10, fontSize: 16, fontWeight: 800, padding: '3px 10px', borderRadius: 6,
                background: live > 0.5 ? C.ok : C.accentSoft, color: live > 0.5 ? '#fff' : C.accent, opacity: 1 - later}}>{live > 0.5 ? 'LIVE' : 'DRAFT'}</span>
              {f >= 92 && <Stamp p={sold} style={{left: 12, top: 12}} />}
              <div style={{fontSize: 20, fontWeight: 700, marginTop: 6}}>{it.name}</div>
            </div>
          );
        })}
      </div>
      <div style={{position: 'absolute', left: 0, right: 0, top: 920, display: 'flex', justifyContent: 'center', opacity: 1 - later}}>
        <div style={{background: clicked ? C.ok : C.accent, color: '#fff', fontSize: 30, fontWeight: 800, borderRadius: 14, padding: '18px 40px',
          transform: `scale(${f > 34 && f < 40 ? 0.95 : 1})`}}>{clicked ? '✓ 14 listings live' : 'Publish 14 reviewed drafts'}</div>
      </div>
      <svg width="44" height="54" viewBox="0 0 22 27" style={{position: 'absolute', left: cx, top: cy, opacity: 1 - fade(f, 60, 70), filter: 'drop-shadow(0 2px 3px rgba(0,0,0,.35))'}}>
        <path d="M1 1 L1 22 L7 16 L11 25 L15 23 L11 15 L19 15 Z" fill="#fff" stroke="#1c1e21" strokeWidth="1.6" strokeLinejoin="round" />
      </svg>
      <Clock f={f} from={66} to={98} />
      {f >= 125 && (
        <div style={{position: 'absolute', right: 80, top: 930, opacity: fade(f, 125, 135), background: C.accent, color: '#fff', borderRadius: 24, padding: '16px 26px', fontSize: 30}}>
          <b style={{opacity: 0.75, fontSize: 21, marginRight: 10}}>You</b>Most of it sold. Update my sales.
        </div>
      )}
    </Scene>
  );
};

// A clock whose hands spin through two weeks, shown over the switch from step 5 to step 6.
const Clock: React.FC<{f: number; from: number; to: number}> = ({f, from, to}) => {
  if (f < from || f > to) return null;
  const t = (f - from) / (to - from);
  const o = Math.min(1, t * 6, (1 - t) * 6);
  const spins = t * 14; // one turn of the hour hand per day
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', background: `rgba(240,242,245,${0.85 * o})`, zIndex: 20}}>
      <div style={{opacity: o, transform: `scale(${0.8 + 0.2 * o})`, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18}}>
        <svg width="300" height="300" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="46" fill="#fff" stroke="#1c1e21" strokeWidth="4" />
          {Array.from({length: 12}, (_, i) => (
            <line key={i} x1="50" y1="9" x2="50" y2={i % 3 ? 13 : 16} stroke="#1c1e21" strokeWidth={i % 3 ? 1.5 : 3} transform={`rotate(${i * 30} 50 50)`} />
          ))}
          <line x1="50" y1="50" x2="50" y2="28" stroke="#1c1e21" strokeWidth="5" strokeLinecap="round" transform={`rotate(${spins * 360} 50 50)`} />
          <line x1="50" y1="50" x2="50" y2="16" stroke="#1877f2" strokeWidth="3" strokeLinecap="round" transform={`rotate(${spins * 360 * 12} 50 50)`} />
          <circle cx="50" cy="50" r="4" fill="#1c1e21" />
        </svg>
        <div style={{fontSize: 44, fontWeight: 800, fontVariantNumeric: 'tabular-nums'}}>Day {Math.min(14, Math.max(1, Math.ceil(spins)))}</div>
      </div>
    </AbsoluteFill>
  );
};

const D = {bg: '#0f1115', panel: '#171a21', line: '#2a2f3e', text: '#e8eaf0', dim: '#8b92a5', accent: '#ffb454', green: '#87d96c', red: '#f07178', blue: '#5ccfe6'};
const SALES: [string, string, string, number, number, boolean][] = [
  ['R116', 'DJI Mavic Air 2', 'eBay', 362.13, 988, true],
  ['R121', 'OnePlus Open', 'Facebook', 400, 1699.99, false],
  ['R117', 'Razer Kishi V3 Pro', 'eBay', 53.96, 149.99, true],
  ['R104', 'Galaxy Buds4', 'eBay', 78.19, 179.99, true],
  ['R108', 'Insta360 X3', 'Facebook', 155, 449.99, false],
  ['R118', 'NuPhy Air75 V2', 'Facebook', 59, 119.95, false],
];
const CHECKS = [
  'Every eBay order matches a record, to the cent',
  'Guessed cost and sale ≥ 60% of it → ask for the receipt',
  'Personal item sold at a loss → not income',
  'Any sale above cost → Form 8949',
  'Loss sales on a 1099-K → backed out on Schedule 1',
];

// Step 7: the sales get recorded, the view flips to tax, checks pass, photos go.
export const Books: React.FC = () => {
  const f = useCurrentFrame();
  const tax = f >= 120;
  const cols = tax ? '80px 1fr 120px 120px 120px 90px' : '80px 1fr 130px 150px 140px';
  return (
    <Scene>
      <Step n={7} title={tax ? 'Close the books' : 'Record the sales'} who={tax ? 'The script writes the tax worksheet, then deletes listing photos' : 'Claude reads each order and chat, then writes the record'} />
      <Robot style={{position: 'absolute', right: 90, top: 40}} size={110} f={f} />
      <Browser url={tax ? '127.0.0.1:8377/#tax' : '127.0.0.1:8377/#live'} label="Resale dashboard" dark typeFrom={-999}
        style={{position: 'absolute', left: 80, top: 180, width: tax ? 1120 : 1760, height: 580}}>
        <div style={{padding: '20px 26px', color: D.text}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 22, marginBottom: 16}}>
            <div style={{fontSize: 28, fontWeight: 800}}>Resale</div>
            <div style={{display: 'flex', gap: 6, background: D.panel, padding: 5, borderRadius: 10, fontSize: 19}}>
              <span style={{padding: '6px 16px', borderRadius: 7, background: tax ? 'none' : D.line, color: tax ? D.dim : D.text}}>For sale</span>
              <span style={{padding: '6px 16px', borderRadius: 7, background: tax ? D.line : 'none', color: tax ? D.text : D.dim}}>Sold & tax</span>
            </div>
            {tax && <span style={{marginLeft: 'auto', color: D.green, fontSize: 19, fontWeight: 700, opacity: fade(f, 200, 210)}}>✓ tax.csv written</span>}
          </div>
          <div style={{display: 'grid', gridTemplateColumns: cols, fontSize: 16, color: D.dim, padding: '6px 10px', borderBottom: `1px solid ${D.line}`}}>
            {tax ? <><span>ID</span><span>Item</span><span style={{textAlign: 'right'}}>Received</span><span style={{textAlign: 'right'}}>Cost</span><span style={{textAlign: 'right'}}>Result</span><span style={{textAlign: 'right'}}>1099-K</span></>
              : <><span>ID</span><span>Item</span><span>Platform</span><span>Status</span><span style={{textAlign: 'right'}}>Received</span></>}
          </div>
          {SALES.map(([id, n, pl, rec, cost, k], i) => {
            const done = f >= 20 + i * 14;
            return (
              <div key={id} style={{display: 'grid', gridTemplateColumns: cols, fontSize: 21, padding: '11px 10px', borderBottom: `1px solid ${D.line}`, fontVariantNumeric: 'tabular-nums', alignItems: 'center'}}>
                <span style={{fontFamily: MONO, color: D.dim, fontSize: 16}}>{id}</span><span>{n}</span>
                {tax ? <>
                  <span style={{textAlign: 'right'}}>{money(rec)}</span><span style={{textAlign: 'right', color: D.dim}}>{money(cost)}</span>
                  <span style={{textAlign: 'right', color: D.red}}>loss</span><span style={{textAlign: 'right', color: D.blue}}>{k ? '✓' : '–'}</span>
                </> : <>
                  <span>{pl}</span>
                  <span><span style={{fontSize: 15, fontWeight: 700, padding: '3px 10px', borderRadius: 6, background: done ? '#3d2326' : D.panel, color: done ? D.red : D.dim}}>{done ? 'SOLD' : 'listed'}</span></span>
                  <span style={{textAlign: 'right', opacity: done ? 1 : 0.2}}>{done ? money(rec) : '—'}</span>
                </>}
              </div>
            );
          })}
        </div>
      </Browser>
      {tax && (
        <Card style={{position: 'absolute', left: 1240, top: 180, right: 80, padding: '18px 22px'}}>
          <div style={{fontSize: 19, fontWeight: 800, color: C.muted, marginBottom: 6}}>CHECKED BEFORE THE TABLE IS WRITTEN</div>
          {CHECKS.map((c, i) => {
            const o = fade(f, 130 + i * 13, 138 + i * 13);
            return (
              <div key={i} style={{display: 'flex', gap: 12, fontSize: 22, lineHeight: 1.3, padding: '9px 0', borderTop: i ? `1px solid ${C.line}` : 'none', opacity: 0.35 + 0.65 * o}}>
                <span style={{color: o > 0.5 ? C.ok : C.muted, fontWeight: 800, width: 24}}>{o > 0.5 ? '✓' : '○'}</span><span>{c}</span>
              </div>
            );
          })}
        </Card>
      )}
      <div style={{position: 'absolute', left: 80, right: 80, bottom: 46, opacity: fade(f, 200, 210)}}>
        <div style={{fontSize: 22, fontWeight: 700, color: C.muted, marginBottom: 10}}>Listing photos deleted. The record stays in git for the IRS’s three years.</div>
        <div style={{display: 'flex', gap: 14}}>
          {items.slice(7, 14).map((it, i) => {
            const s = fade(f, 212 + i * 6, 226 + i * 6);
            return (
              <div key={it.uid} style={{flex: 1, height: 70, borderRadius: 12, background: s > 0.5 ? C.card : C.waitSoft, display: 'flex', alignItems: 'center', gap: 10, padding: '0 14px',
                fontFamily: MONO, fontSize: 16, boxShadow: '0 1px 3px rgba(0,0,0,.12)', overflow: 'hidden', whiteSpace: 'nowrap'}}>
                {s < 0.5
                  ? <><span style={{width: 30, height: 22, borderRadius: '4px 4px 6px 6px', background: C.wait, flex: 'none'}} /><span>{it.uid}/photos · {it.photos.length}</span></>
                  : <><span style={{color: C.ok, fontWeight: 800}}>✓</span><span>2026/{it.uid}.yaml</span></>}
              </div>
            );
          })}
        </div>
      </div>
    </Scene>
  );
};

export const End: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: f, fps, config: {damping: 26, mass: 1.3}});
  const s = spring({frame: f - 20, fps, config: {damping: 26}});
  return (
    <Scene>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', gap: 26}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 26, opacity: p, transform: `scale(${0.88 + 0.12 * p})`}}>
          <div style={{width: 120, height: 120, borderRadius: 60, background: C.accent, color: '#fff', display: 'grid', placeItems: 'center', fontSize: 64, fontWeight: 800}}>R</div>
          <div style={{fontSize: 128, fontWeight: 800, letterSpacing: '-0.04em'}}>Resale Hub</div>
        </div>
        <div style={{fontSize: 38, color: C.muted, opacity: s}}>Take the pictures. It handles the rest, up to Publish.</div>
        <div style={{marginTop: 18, fontSize: 30, fontWeight: 700, color: '#fff', background: C.accent, borderRadius: 16, padding: '16px 32px', opacity: s}}>
          github.com/doriru89/resale-hub
        </div>
      </AbsoluteFill>
    </Scene>
  );
};
