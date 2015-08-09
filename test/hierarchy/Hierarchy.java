public class Hierarchy
{
    public int bar(HierarchyA obj)
    {
        return obj.foo(5);
    }

    public static void main(String args[])
    {
        HierarchyA obj = new HierarchyB();
        System.out.println(new Hierarchy().bar(obj));
    }
}
