import itertools, json, os, math
from collections import deque, Counter

class ReturnToMenu(Exception):
    """Raised when user wants to return to main menu."""
    pass

# ==================== CONSTANTS ====================
MOVES = [-15, -9, -6, -3, 2, 7, 13, 16]   # possible anvil moves
H_OPTS = [-3, -6, -9]                     # 'any hit' options

# ==================== UTILITY FUNCTIONS ====================

def gi(p, l, h):
    """Get integer input between l and h, with 'M' to return to menu."""
    while 1:
        i = input(p).strip()
        if i.lower() == 'm':
            raise ReturnToMenu()
        try:
            v = int(i)
            if l <= v <= h:
                return v
            print(f"Value between {l} and {h}.")
        except:
            print("Invalid integer.")

def pa(s):
    """Parse amount string like '10 i', '450 mb' or '20' into mb and display string."""
    s = s.strip().lower()
    if s == 'm':
        raise ReturnToMenu()
    if s.endswith(' mb'):
        return int(float(s[:-3])), s
    if s.endswith(' i'):
        return int(float(s[:-2]) * 100), s
    try:
        return int(float(s) * 100), f"{s} i"
    except:
        print("Invalid amount.")
        raise

def fm(m):
    """Format mb amount into briquets/pellets/powder for readability."""
    b, pd, pw = 80, 20, 5
    nb, r = divmod(m, b)
    np, r = divmod(r, pd)
    nw, r = divmod(r, pw)
    parts = [f"{m} mb"]
    for n, na in ((nb, "briquet"), (np, "pellet"), (nw, "powder")):
        if n:
            parts.append(f"{n} {na}{'s' * (n > 1)}")
    if r:
        parts.append(f"{r} mb leftover")
    return " (" + ", ".join(parts) + ")"

def yn(p):
    """Ask yes/no question, return True for y/yes, False for n/no, 'M' raises ReturnToMenu."""
    while 1:
        a = input(p).strip().lower()
        if a == 'm':
            raise ReturnToMenu()
        if a in ('y', 'yes'):
            return True
        if a in ('n', 'no'):
            return False
        print("Answer y/n or M.")

# ==================== ANVIL HELP ====================

def bfs(t, b=1000):
    """BFS to find minimum moves to reach target t from 0 using MOVES. Returns (moves, path)."""
    if t == 0:
        return 0, []
    d, p = {0: 0}, {}
    q = deque([0])
    while q:
        c = q.popleft()
        for m in MOVES:
            n = c + m
            if abs(n) <= b and n not in d:
                d[n] = d[c] + 1
                p[n] = (c, m)
                if n == t:
                    path = []
                    s = t
                    while s != 0:
                        path.append(p[s][1])
                        s = p[s][0]
                    return d[t], path[::-1]
                q.append(n)
    return None, None

def anvil():
    """Anvil helper: find sequence of hits to change start value to target with 3 mandatory last moves."""
    print("\n" + "=" * 50 + "\nANVIL HELP\n" + "=" * 50 + "\nAllowed moves: -15,-9,-6,-3,+2,+7,+13,+16\n")
    s = gi("Start (0-150): ", 0, 150)
    t = gi("Target (0-150): ", 0, 150)
    d = t - s

    print("\nEnter three mandatory last moves.\n  Use +16/-3, 'H' for any hit, 'N' for any move\n")

    def gmo(p):
        """Get mandatory move options: specific move, H (any hit), or N (any move)."""
        while 1:
            i = input(p).strip().upper()
            if i == 'M':
                raise ReturnToMenu()
            if i == 'H':
                return H_OPTS
            if i == 'N':
                return MOVES
            try:
                v = int(i.replace('+', ''))
                if v in MOVES:
                    return [v]
                print(f"Invalid. Allowed {MOVES}")
            except:
                print(f"Invalid.")

    opts = [gmo(f"Move {i+1} ({['antepenultimate','penultimate','last'][i]}): ") for i in range(3)]

    best, best_len = None, float('inf')
    total = 1
    for o in opts:
        total *= len(o)
    print(f"\nSearching {total} combos...")

    for m1, m2, m3 in itertools.product(*opts):
        pref = d - (m1 + m2 + m3)
        cnt, pth = bfs(pref)
        if cnt is not None and cnt + 3 < best_len:
            best_len = cnt + 3
            best = (pth, [m1, m2, m3])

    if not best:
        print("\nNo solution!")
        return

    pfx, man = best
    print("\n" + "=" * 40 + "\nSOLUTION\n" + "=" * 40 + f"\nStart {s} -> Target {t}\nTotal moves {best_len}")
    if pfx:
        print("\nPrefix moves:")
        for mv, cnt in Counter(pfx).items():
            print(f"   • {cnt} hit{'s' * (cnt > 1)} to {mv:+d}")
    else:
        print("\nNo prefix.")

    print("\nMandatory last moves:")
    for i, mv in enumerate(man, 1):
        print(f"   {i}. 1 hit to {mv:+d}")
    print("\n" + "=" * 40)

# ==================== ALLOY HELPER ====================

def load_alloys(f="alloys.json"):
    """Load alloys from JSON file; create default if missing."""
    if not os.path.exists(f):
        d = [{"name": "Bronze", "type": "alloy", "elements": [{"name": "Copper", "min": 88, "max": 92},
                                                              {"name": "Tin", "min": 8, "max": 12}]}]
        with open(f, "w") as fp:
            json.dump(d, fp, indent=2)
        return d
    with open(f) as fp:
        return json.load(fp)

def is_comp(m):
    """Return True if material is a composite (not a simple alloy)."""
    return m.get('type') == 'composite'

def ask_pct(e, ind=""):
    """Ask user for percentages of each element (within min/max) until total = 100%."""
    while 1:
        pcts, tot = [], 0.0
        for el in e:
            while 1:
                i = input(f"{ind}% of {el['name']} ({el['min']}-{el['max']}%): ").strip()
                if i.lower() == 'm':
                    raise ReturnToMenu()
                try:
                    p = float(i)
                    if el['min'] <= p <= el['max']:
                        break
                    print(f"{ind}Value {el['min']}-{el['max']}.")
                except:
                    print(f"{ind}Invalid number.")
            pcts.append(p)
            tot += p
            if tot > 100.001:
                print(f"{ind}Total >100% restart.")
                break
        else:
            if abs(tot - 100) <= 0.001:
                return pcts
            print(f"{ind}Sum {tot}%, need {100 - tot:.1f}% more.")

def get_recipe(a, depth=0):
    """Extract the list of elements (with min/max) from an alloy, handling multiple recipes."""
    ind = "  " * depth
    if "recipes" in a and len(a["recipes"]) > 1:
        print(f"{ind}Multiple recipes for {a['name']}:")
        for i, r in enumerate(a["recipes"], 1):
            print(f"{ind}  {i}. {', '.join(e['name'] for e in r['elements'])}")
        while 1:
            try:
                c = int(input(f"{ind}Choose recipe: "))
                if 1 <= c <= len(a["recipes"]):
                    return a["recipes"][c - 1]["elements"]
            except:
                pass
            print(f"{ind}Invalid.")
    if "recipes" in a and len(a["recipes"]) == 1:
        return a["recipes"][0]["elements"]
    if "elements" in a:
        return a["elements"]
    raise ValueError(f"{a['name']} has no elements/recipes.")

def select_alloy(alloys, ps=10):
    """Interactive paginated selection of an alloy, with search by name."""
    fl = alloys
    page = 0
    search = False

    def tp(l):
        return max(1, math.ceil(len(l) / ps))

    def disp(l, p, tp_):
        s = p * ps
        e = min(s + ps, len(l))
        print(f"\n--- Page {p + 1}/{tp_} ({len(l)} items) ---")
        for idx, al in enumerate(l[s:e], start=s + 1):
            print(f"  {idx}. {al['name']}")
        if not search:
            print("  [n]next [p]prev [M]menu\n  or enter number or part of name")
        else:
            print("  [n]next [p]prev [b]back [M]menu\n  or enter number")

    while 1:
        tpp = tp(fl)
        if page >= tpp:
            page = tpp - 1
        disp(fl, page, tpp)
        i = input("Select alloy: ").strip().lower()
        if i == 'm':
            raise ReturnToMenu()
        if i == 'n':
            if page + 1 < tpp:
                page += 1
            else:
                print("Last page.")
            continue
        if i == 'p':
            if page > 0:
                page -= 1
            else:
                print("First page.")
            continue
        if i == 'b':
            if search:
                fl, search, page = alloys, False, 0
                continue
            else:
                print("Not in search.")
                continue
        try:
            num = int(i)
            if 1 <= num <= len(fl):
                return fl[num - 1]
            print(f"Number 1-{len(fl)}.")
            continue
        except:
            pass
        matches = [a for a in alloys if i in a['name'].lower()]
        if not matches:
            print(f"No alloy contains '{i}'.")
            continue
        fl, search, page = matches, True, 0

def decompose(alloys, name, mb, depth=0):
    """Recursively break down an alloy or composite into its base materials."""
    ind = "  " * depth
    mat = next((a for a in alloys if a['name'].lower() == name.lower()), None)
    if mat is None:
        print(f"{ind}• {name}: {mb:.0f} mb{fm(int(round(mb)))}")
        return

    typ = "Composite" if is_comp(mat) else "Alloy"
    print(f"{ind}{typ} '{name}' needs {mb:.0f} mb{fm(int(round(mb)))}.")
    if not yn(ind + "Break down? (y/n): "):
        print(f"{ind}  -> Use {mb:.0f} mb of {name}.")
        return

    if is_comp(mat):
        comps = mat['components']
        tot_r = sum(c['ratio'] for c in comps)
        for c in comps:
            decompose(alloys, c['name'], mb * c['ratio'] / tot_r, depth + 1)
        return

    elems = get_recipe(mat, depth)
    print(f"{ind}Enter composition for '{name}':")
    pcts = ask_pct(elems, ind + "  ")
    for e, p in zip(elems, pcts):
        decompose(alloys, e['name'], mb * p / 100, depth + 1)

def alloy():
    """Alloy helper: compute required base materials, split into crucibles, decompose sub-alloys."""
    print("\n" + "=" * 50 + "\nALLOY HELPER\n" + "=" * 50)
    alloys = load_alloys()
    a = select_alloy(alloys)
    if a is None:
        print("Cancelled.")
        return

    amt_str = input("Amount (e.g., '10 i', '450 mb', '20'): ")
    amb, adis = pa(amt_str)

    elems = get_recipe(a)      # get recipe elements for this alloy
    pcts = ask_pct(elems)

    print("\n" + "=" * 40 + "\nRESULTS\n" + "=" * 40 + f"\nTotal alloy: {adis} = {amb} mb\n\nYou need to add:")
    comps = []
    for e, p in zip(elems, pcts):
        need = amb * p / 100
        comps.append((e['name'], need))
        print(f"  • {e['name']}: {need:.2f} mb{fm(int(round(need)))} ({p}%)")

    # Split into crucibles if >3000 mb
    if amb > 3000 and yn("\nExceeds crucible (30i/3000mb). Split into multiple? (y/n): "):
        print("\n" + "=" * 40 + "\nCRUCIBLE SPLIT\n" + "=" * 40)
        rem = amb
        idx = 1
        while rem > 0:
            batch = min(3000, rem)
            print(f"\nCRUCIBLE #{idx} ({batch:.0f} mb)\n" + "-" * 32)
            for e, p in zip(elems, pcts):
                comp = round(batch * p / 100)
                print(f"{e['name']}: {comp:.0f} mb{fm(comp)}")
            rem -= batch
            idx += 1

    # Decompose any sub-alloys if user agrees
    anames = [a['name'].lower() for a in alloys]
    has_sub = any(n.lower() in anames for n, _ in comps)
    if has_sub and yn("\nDecompose sub-alloys? (y/n): "):
        for n, need in comps:
            if any(a['name'].lower() == n.lower() for a in alloys):
                print(f"\n--- Decomposing {n} (need {need:.2f} mb) ---")
                decompose(alloys, n, need)

    print("\n" + "=" * 40)

# ==================== MAIN MENU ====================

def main():
    """Main menu loop."""
    while 1:
        try:
            # Appealing header with credit
            print("\n" + "╔" + "═" * 48 + "╗")
            print("║" + " " * 12 + "App created by Juanakin01" + " " * 11 + "║")
            print("╠" + "═" * 48 + "╣")
            print("║" + " " * 18 + "MAIN MENU" + " " * 21 + "║")
            print("╠" + "═" * 48 + "╣")
            print("║" + " " * 4 + "1.Anvil Helper" + " " * 30 + "║")
            print("║" + " " * 4 + "2.Alloy Helper" + " " * 30 + "║")
            print("║" + " " * 4 + "3.Exit" + " " * 38 + "║")
            print("╚" + "═" * 48 + "╝")
            print("─" * 50)
            c = input("➡️  Select option (1-3): ").strip()
            match c:
                case '1':
                    anvil()
                    input("\nPress Enter to continue...")
                case '2':
                    alloy()
                    input("\nPress Enter to continue...")
                case '3':
                    print("\n Goodbye! Thanks for using the app.")
                    break
                case _:
                    print("\n Invalid option. Please enter 1, 2 or 3.")
        except ReturnToMenu:
            print("\nReturning to main menu...")
            continue
        except KeyboardInterrupt:
            print("\n\nProgram interrupted. Goodbye!")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted.")