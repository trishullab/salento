public class HierarchyC
{
    public int foo(int i)
    {
        Boolean b;
        if (i > 10)
            b = new Boolean(true);
        else
            b = new Boolean(false);
        System.out.println(b);
        return i + 3;
    }
}
