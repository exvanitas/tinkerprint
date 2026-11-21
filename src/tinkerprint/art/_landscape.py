"""Two little night landscapes, cut into broad bands of close-valued ink."""
from ._drawing import Drawing


def pine(d, x, y, size, shade):
    """A wind-pruned fir, growing up from (x, y)."""
    w = size // 3
    d.shape(shade, (x, y-size), (x+w-1, y-size//2), (x+w-2, y-size//2),
            (x+w, y-2), (x+1, y-3), (x+1, y), (x-1, y), (x-1, y-3),
            (x-w, y-1), (x-w+1, y-size//2+1), (x-w+2, y-size//2+1))


def valley(set_name):
    d = Drawing()
    if set_name == 'builder':
        d.rect(0, 0, 48, 48, '?')
        # Cold light on the ridge and the arches of a distant viaduct.
        d.grid(1, 3, """
   MM
  ss
 ss
 ss
  ss  M
   ssM
""")
        d.shape('%', (0, 27), (10, 19), (14, 21), (22, 15), (31, 22),
                (36, 18), (39, 19), (47, 12), (47, 40), (0, 40))
        d.grid(39, 12, """
        /
       //
     ///%
    //%%
   //%
""")
        d.grid(0, 26, """
//////////////
!!!!!!!!!!!!!!
!!??!!!??!!!??
!???!!????!!??
!???!!????!!??
!??!!!????!!!
""")
        d.shape('!', (0, 33), (9, 35), (17, 34), (27, 37), (39, 33),
                (47, 29), (47, 47), (0, 47))
        d.shape('%', (0, 42), (7, 40), (16, 39), (30, 40), (42, 39),
                (47, 40), (47, 44), (33, 44), (12, 45), (0, 45))
        d.line('/', (0, 42), (6, 40), (11, 40))
        d.line('?', (37, 43), (42, 42), (47, 42))
        frame, rim = '!', '%'
    else:
        d.rect(0, 0, 48, 48, '}')
        # A low harvest moon, broken reflection and rushes at the water's edge.
        d.grid(1, 3, """
    xxx
   x000x
  x00000x
  x00000x
   x000x
 ;;xxxx;;;
     ;;
""")
        d.shape('|', (0, 22), (5, 20), (13, 23), (21, 19), (30, 25),
                (39, 22), (47, 18), (47, 39), (0, 39))
        d.rect(0, 29, 48, 8, ';')
        d.rect(0, 30, 11, 1, '|')
        d.rect(3, 32, 6, 1, 'x')
        d.rect(2, 34, 3, 1, '|')
        d.shape('{', (0, 37), (7, 35), (14, 36), (25, 35), (34, 37),
                (43, 33), (47, 32), (47, 47), (0, 47))
        d.grid(41, 24, """
     {
  {  {
  {  {
  { {    {
   {{   {
    {  {
   {{{{
    {{
    {{{
""")
        d.shape('|', (0, 42), (11, 39), (26, 40), (36, 39), (47, 39),
                (47, 44), (36, 43), (16, 45), (0, 45))
        d.line(';', (0, 42), (7, 40), (11, 40))
        d.line('}', (38, 43), (42, 42), (47, 42))
        frame, rim = '{', '|'
    # Clipped corners and a single ruled edge, like the ink of a small bookplate.
    for y, inset in enumerate((5, 3, 2, 1, 1)):
        d.rect(0, y, inset, 1, frame)
        d.rect(48 - inset, y, inset, 1, frame)
    d.rect(2, 46, 44, 1, rim)
    # The same plane carries the heels of all thirteen guild members.
    d.shape(frame, (10, 42), (16, 41), (29, 41), (36, 42),
            (32, 43), (14, 44), (10, 43))
    return d.part()
