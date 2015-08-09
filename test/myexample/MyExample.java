import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;

public class MyExample
{
    int a1() {
        return 1;
    }
    
    int a2() {
        return 2;
    }

    int b1() {
        return 1;
    }
    
    int b2() {
        return 2;
    }

    int c1() {
        return 1;
    }
    
    int c2() {
        return 2;
    }

    public int myCallbackFn() {
        return 555;
    }

    public static void main(String args[]) throws IOException
    {
        MyExample m = new MyExample();
//        String [] my_args = new String [3];
//        my_args[0] = args[0];
//        my_args[1] = args[1];
//        my_args[2] = args[2];
//
//        boolean b1, b2, b3;
//
//        if (my_args[0].equals("f"))
//            b1 = false;
//        else
//            b1 = true;
//        if (my_args[1].equals("f"))
//            b2 = false;
//        else
//            b2 = true;
//        if (my_args[2].equals("f"))
//            b3 = false;
//        else
//            b3 = true;
//        
//        m.myExampleTest(b1, b2, b3);
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        String s;
        MyBool b1, b2, b3;
        s = br.readLine();
        if (s.equals("f"))
            b1 = new MyBool(false);
        else
            b1 = new MyBool(true);
        s = br.readLine();
        if (s.equals("f"))
            b2 = new MyBool(false);
        else
            b2 = new MyBool(true);
        s = br.readLine();
        if (s.equals("f"))
            b3 = new MyBool(false);
        else
            b3 = new MyBool(true);
        boolean r = m.myExampleTest(b1, b2, b3);

    }

    boolean myExampleTest(MyBool b1, MyBool b2, MyBool b3)
    {
        int s = 0;
        boolean a = b1.getA();
        boolean b = b2.getA();
        boolean c = b3.getA();

        if (a) {
            s += a1();
        }
        else {
            s += a2();
        }

        if (b) {
            s += b1();
        }
        else {
            s += b2();
        }

        if (a && !b) {
            s += c1();
        }
        else {
            s += c2();
        }

        System.out.println(s);
        return c;
    }
}
