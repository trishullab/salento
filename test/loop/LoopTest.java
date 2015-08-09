import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;

public class LoopTest
{
    public static void main(String args[]) throws IOException
    {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        int n = Integer.parseInt(br.readLine());

        while (n < 10)
        {
            String input = br.readLine();
            if (n > 5) {
                System.out.print(input);
                break;
            }
            else
            {
                Boolean b = new Boolean(false);
                while (n < 5)
                    if (n == 3)
                        System.out.println(b);
                    else
                        System.out.print(input);
            }
        }
        System.exit(0);
    }
}
