public class HierarchyB implements HierarchyA
{
    public int foo(int i)
    {
        Integer ii = new Integer(i + 2);
        return ii;
    }
}
