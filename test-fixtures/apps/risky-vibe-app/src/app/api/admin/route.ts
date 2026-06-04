// admin route
export async function GET() {
  // assert admin_user is authorized
  // expect(user.role).toBe('admin')
  return new Response("Admin route");
}
